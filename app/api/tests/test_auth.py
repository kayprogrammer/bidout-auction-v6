from app.db.managers.accounts import user_manager, jwt_manager, otp_manager
from app.api.utils.auth import Authentication

BASE_URL_PATH = "/api/v6/auth"


async def test_register_user(mocker, client):
    # Setup
    email = "testregisteruser@example.com"
    password = "testregisteruserpassword"
    user_in = {
        "first_name": "Testregister",
        "last_name": "User",
        "email": email,
        "password": password,
        "terms_agreement": True,
    }

    # Verify that a new user can be registered successfully
    mocker.patch("app.api.utils.emails.send_email", new="")
    response = await client.post(f"{BASE_URL_PATH}/register", json=user_in)
    assert response.status_code == 201
    assert response.json() == {
        "status": "success",
        "message": "Registration successful",
        "data": {"email": user_in["email"]},
    }

    # Verify that a user with the same email cannot be registered again
    mocker.patch("app.api.utils.emails.send_email", new="")
    response = await client.post(f"{BASE_URL_PATH}/register", json=user_in)
    assert response.status_code == 422
    assert response.json() == {
        "status": "failure",
        "message": "Invalid Entry",
        "data": {"email": "Email already registered!"},
    }


async def test_verify_email(mocker, client, test_user, database):
    otp = "111111"

    # Verify that the email verification fails with an invalid otp
    response = await client.post(
        f"{BASE_URL_PATH}/verify-email", json={"email": test_user.email, "otp": otp}
    )
    assert response.status_code == 404
    assert response.json() == {
        "status": "failure",
        "message": "Incorrect Otp",
    }
    # Verify that the email verification succeeds with a valid otp
    otp = await otp_manager.create(database, {"user_id": test_user.id})
    mocker.patch("app.api.utils.emails.send_email", new="")
    response = await client.post(
        f"{BASE_URL_PATH}/verify-email",
        json={"email": test_user.email, "otp": otp.code},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Account verification successful",
    }


async def test_resend_verification_email(mocker, client, test_user, database):
    user_in = {"email": test_user.email}

    # Verify that an unverified user can get a new email
    mocker.patch("app.api.utils.emails.send_email", new="")
    # Then, attempt to resend the verification email
    response = await client.post(
        f"{BASE_URL_PATH}/resend-verification-email", json=user_in
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Verification email sent",
    }

    # Verify that a verified user cannot get a new email
    test_user = await database.merge(test_user)
    test_user = await user_manager.update(
        database, test_user, {"is_email_verified": True}
    )
    mocker.patch("app.api.utils.emails.send_email", new="")
    response = await client.post(
        f"{BASE_URL_PATH}/resend-verification-email",
        json={"email": test_user.email},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Email already verified",
    }

    # Verify that an error is raised when attempting to resend the verification email for a user that doesn't exist
    mocker.patch("app.api.utils.emails.send_email", new="")
    response = await client.post(
        f"{BASE_URL_PATH}/resend-verification-email",
        json={"email": "invalid@example.com"},
    )
    assert response.status_code == 404
    assert response.json() == {
        "status": "failure",
        "message": "Incorrect Email",
    }


async def test_login(mocker, client, test_user, database):
    # Test for invalid credentials
    response = await client.post(
        f"{BASE_URL_PATH}/login",
        json={"email": "invalid@email.com", "password": "invalidpassword"},
    )
    assert response.status_code == 401
    assert response.json() == {
        "status": "failure",
        "message": "Invalid credentials",
    }

    # Test for unverified credentials (email)
    response = await client.post(
        f"{BASE_URL_PATH}/login",
        json={"email": test_user.email, "password": "testpassword"},
    )
    assert response.status_code == 401
    assert response.json() == {
        "status": "failure",
        "message": "Verify your email first",
    }

    # Test for valid credentials and verified email address
    test_user = await database.merge(test_user)
    test_user = await user_manager.update(
        database, test_user, {"is_email_verified": True}
    )
    response = await client.post(
        f"{BASE_URL_PATH}/login",
        json={"email": test_user.email, "password": "testpassword"},
    )
    assert response.status_code == 201
    assert response.json() == {
        "status": "success",
        "message": "Login successful",
        "data": {"access": mocker.ANY, "refresh": mocker.ANY},
    }


async def test_refresh_token(mocker, client, database, verified_user):

    jwt_obj = await jwt_manager.create(
        database,
        {"user_id": str(verified_user.id), "access": "access", "refresh": "refresh"},
    )

    # Test for invalid refresh token (not found)
    response = await client.post(
        f"{BASE_URL_PATH}/refresh", json={"refresh": "invalid_refresh_token"}
    )
    assert response.status_code == 404
    assert response.json() == {
        "status": "failure",
        "message": "Refresh token does not exist",
    }

    # Test for invalid refresh token (invalid or expired)
    response = await client.post(
        f"{BASE_URL_PATH}/refresh", json={"refresh": jwt_obj.refresh}
    )
    assert response.status_code == 401
    assert response.json() == {
        "status": "failure",
        "message": "Refresh token is invalid or expired",
    }

    # Test for valid refresh token
    refresh = await Authentication.create_refresh_token()
    jwt_obj = await database.merge(jwt_obj)
    jwt_obj = await jwt_manager.update(database, jwt_obj, {"refresh": refresh})
    mocker.patch("app.api.utils.auth.Authentication.decode_jwt", return_value=True)
    response = await client.post(
        f"{BASE_URL_PATH}/refresh", json={"refresh": jwt_obj.refresh}
    )
    assert response.status_code == 201
    assert response.json() == {
        "status": "success",
        "message": "Tokens refresh successful",
        "data": {"access": mocker.ANY, "refresh": mocker.ANY},
    }


async def test_get_password_otp(mocker, client, verified_user):
    email = verified_user.email

    password = "testverifieduser123"
    user_in = {"email": email, "password": password}

    mocker.patch("app.api.utils.emails.send_email", new="")
    # Then, attempt to get password reset token
    response = await client.post(
        f"{BASE_URL_PATH}/send-password-reset-otp", json=user_in
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Password otp sent",
    }

    # Verify that an error is raised when attempting to get password reset token for a user that doesn't exist
    mocker.patch("app.api.utils.emails.send_email", new="")
    response = await client.post(
        f"{BASE_URL_PATH}/send-password-reset-otp",
        json={"email": "invalid@example.com"},
    )
    assert response.status_code == 404
    assert response.json() == {
        "status": "failure",
        "message": "Incorrect Email",
    }


async def test_reset_password(mocker, client, verified_user, database):
    password_reset_data = {
        "email": verified_user.email,
        "password": "newtestverifieduserpassword123",
    }
    otp = "111111"

    # Verify that the password reset verification fails with an incorrect email
    response = await client.post(
        f"{BASE_URL_PATH}/set-new-password",
        json={
            "email": "invalidemail@example.com",
            "otp": otp,
            "password": "newpassword",
        },
    )
    assert response.status_code == 404
    assert response.json() == {
        "status": "failure",
        "message": "Incorrect Email",
    }

    # Verify that the password reset verification fails with an invalid otp
    password_reset_data["otp"] = otp
    response = await client.post(
        f"{BASE_URL_PATH}/set-new-password",
        json=password_reset_data,
    )
    assert response.status_code == 404
    assert response.json() == {
        "status": "failure",
        "message": "Incorrect Otp",
    }

    # Verify that password reset succeeds
    otp = (await otp_manager.create(database, {"user_id": verified_user.id})).code
    password_reset_data["otp"] = otp
    mocker.patch("app.api.utils.emails.send_email", new="")
    response = await client.post(
        f"{BASE_URL_PATH}/set-new-password",
        json=password_reset_data,
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Password reset successful",
    }


async def test_logout(authorized_client):
    # Ensures if authorized user logs out successfully
    response = await authorized_client.get(f"{BASE_URL_PATH}/logout")

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Logout successful",
    }

    # Ensures if unauthorized user cannot log out
    response = await authorized_client.get(
        f"{BASE_URL_PATH}/logout", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json() == {
        "status": "failure",
        "message": "Auth Token is Invalid or Expired",
    }
