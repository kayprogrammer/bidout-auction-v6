from app.db.managers.accounts import jwt_manager
from app.db.managers.listings import category_manager, watchlist_manager, bid_manager
from app.api.utils.auth import Authentication

BASE_URL_PATH = "/api/v6/listings"


async def test_retrieve_all_listings(client, create_listing):
    # Verify that all listings are retrieved successfully
    response = await client.get(BASE_URL_PATH)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["message"] == "Listings fetched"
    data = result["data"]
    assert len(data) > 0
    assert any(isinstance(obj["name"], str) for obj in data)


async def test_retrieve_particular_listng(mocker, client, create_listing):
    listing = create_listing["listing"]

    # Verify that a particular listing retrieval fails with an invalid slug
    response = await client.get(f"{BASE_URL_PATH}/detail/invalid_slug")
    assert response.status_code == 404
    assert response.json() == {
        "status": "failure",
        "message": "Listing does not exist!",
    }

    # Verify that a particular listing is retrieved successfully
    response = await client.get(f"{BASE_URL_PATH}/detail/{listing.slug}")
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Listing details fetched",
        "data": {
            "listing": {
                "name": listing.name,
                "auctioneer": mocker.ANY,
                "slug": listing.slug,
                "desc": listing.desc,
                "category": "TestCategory",
                "price": mocker.ANY,
                "closing_date": mocker.ANY,
                "time_left_seconds": mocker.ANY,
                "active": True,
                "bids_count": 0,
                "highest_bid": 0.0,
                "image": mocker.ANY,
                "watchlist": None,
            },
            "related_listings": [],
        },
    }


async def test_get_user_watchlists_listng(authorized_client, create_listing, database):
    listing = create_listing["listing"]
    user_id = create_listing["user"].id
    await watchlist_manager.create(
        database, {"user_id": str(user_id), "listing_id": listing.id}
    )

    response = await authorized_client.get(f"{BASE_URL_PATH}/watchlist")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["message"] == "Watchlist Listings fetched"
    data = result["data"]
    assert len(data) > 0
    assert any(isinstance(obj["name"], str) for obj in data)


async def test_create_or_remove_user_watchlists_listng(
    authorized_client, create_listing, mocker
):
    listing = create_listing["listing"]

    # Verify that the endpoint fails with an invalid slug
    response = await authorized_client.post(
        f"{BASE_URL_PATH}/watchlist", json={"slug": "invalid_slug"}
    )
    assert response.status_code == 404
    assert response.json() == {
        "status": "failure",
        "message": "Listing does not exist!",
    }

    # Verify that the watchlist was created successfully
    response = await authorized_client.post(
        f"{BASE_URL_PATH}/watchlist", json={"slug": listing.slug}
    )
    assert response.status_code == 201
    assert response.json() == {
        "status": "success",
        "message": "Listing added to user watchlist",
        "data": {"guestuser_id": mocker.ANY},
    }


async def test_retrieve_all_categories(client, database):
    # Create Category
    await category_manager.create(database, {"name": "TestCategory"})

    # Verify that all categories are retrieved successfully
    response = await client.get(f"{BASE_URL_PATH}/categories")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["message"] == "Categories fetched"
    data = result["data"]
    assert len(data) > 0
    assert any(isinstance(obj["name"], str) for obj in data)


async def test_retrieve_all_listings_by_category(client, create_listing):
    slug = create_listing["category"].slug

    # Verify that listings by an invalid category slug fails
    response = await client.get(f"{BASE_URL_PATH}/categories/invalid_category_slug")
    assert response.status_code == 404
    assert response.json() == {"status": "failure", "message": "Invalid category"}

    # Verify that all listings by a valid category slug are retrieved successfully
    response = await client.get(f"{BASE_URL_PATH}/categories/{slug}")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["message"] == "Category Listings fetched"
    data = result["data"]
    assert len(data) > 0
    assert any(isinstance(obj["name"], str) for obj in data)


async def test_retrieve_listing_bids(
    client, create_listing, another_verified_user, database
):
    listing = create_listing["listing"]

    await bid_manager.create(
        database,
        {
            "user_id": another_verified_user.id,
            "listing_id": listing.id,
            "amount": 10000,
        },
    )

    # Verify that listings by an invalid listing slug fails
    response = await client.get(f"{BASE_URL_PATH}/detail/invalid_category_slug/bids")
    assert response.status_code == 404
    assert response.json() == {
        "status": "failure",
        "message": "Listing does not exist!",
    }

    # Verify that all listings by a valid listing slug are retrieved successfully
    response = await client.get(f"{BASE_URL_PATH}/detail/{listing.slug}/bids")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["message"] == "Listing Bids fetched"
    data = result["data"]
    assert isinstance(data["listing"], str)


async def test_create_bid(
    authorized_client, create_listing, another_verified_user, database, mocker
):
    listing = create_listing["listing"]

    # Verify that the endpoint fails with an invalid slug
    response = await authorized_client.post(
        f"{BASE_URL_PATH}/detail/invalid_listing_slug/bids", json={"amount": 10000}
    )
    assert response.status_code == 404
    assert response.json() == {
        "status": "failure",
        "message": "Listing does not exist!",
    }

    # Verify that the endpoint fails with an invalid user
    response = await authorized_client.post(
        f"{BASE_URL_PATH}/detail/{listing.slug}/bids", json={"amount": 10000}
    )
    assert response.status_code == 403
    assert response.json() == {
        "status": "failure",
        "message": "You cannot bid your own product!",
    }

    # Update headers with another user's token
    access = await Authentication.create_access_token(
        {"user_id": str(another_verified_user.id)}
    )
    refresh = await Authentication.create_refresh_token()
    await jwt_manager.create(
        database,
        {"user_id": another_verified_user.id, "access": access, "refresh": refresh},
    )
    authorized_client.headers = {"Authorization": f"Bearer {access}"}

    # Verify that the endpoint fails with a lesser bidding price
    response = await authorized_client.post(
        f"{BASE_URL_PATH}/detail/{listing.slug}/bids", json={"amount": 100}
    )
    assert response.status_code == 400
    assert response.json() == {
        "status": "failure",
        "message": "Bid amount cannot be less than the bidding price!",
    }

    # Verify that the bid was created successfully
    response = await authorized_client.post(
        f"{BASE_URL_PATH}/detail/{listing.slug}/bids", json={"amount": 10000}
    )
    assert response.status_code == 201
    assert response.json() == {
        "status": "success",
        "message": "Bid added to listing",
        "data": {
            "user": mocker.ANY,
            "amount": 10000.0,
            "created_at": mocker.ANY,
            "updated_at": mocker.ANY,
        },
    }

    # You can also test for other error responses.....
