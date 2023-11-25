# BIDOUT AUCTION V6

![alt text](https://github.com/kayprogrammer/bidout-auction-v6/blob/main/display/fastapi.png?raw=true)


#### FASTAPI DOCS: [Documentation](https://fastapi.tiangolo.com/)

#### PG ADMIN: [Documentation](https://pgadmin.org) 


## How to run locally

* Download this repo or run: 
```bash
    $ git clone git@github.com:kayprogrammer/bidout-auction-v6.git
```

#### In the root directory:
- Install all dependencies
```bash
    $ pip install -r requirements.txt
```
- Create an `.env` file and copy the contents from the `.env.example` to the file and set the respective values. A postgres database can be created with PG ADMIN or psql

- Run Locally
```bash
    $ alembic upgrade heads 
```
```bash
    $ uvicorn app.main:app --debug --reload
```

- Run With Docker
```bash
    $ docker-compose up --build -d --remove-orphans
```
OR
```bash
    $ make build
```

- Test Coverage
```bash
    $ pytest --disable-warnings -vv
```
OR
```bash
    $ make test
```

## Docs
#### API Url: [BidOut Docs](https://bidout-fastapi.vercel.app/) 
#### Swagger: [Documentation](https://swagger.io/docs/)

![alt text](https://github.com/kayprogrammer/bidout-auction-v6/blob/main/display/display1.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v6/blob/main/display/display2.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v6/blob/main/display/display3.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v6/blob/main/display/display4.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v6/blob/main/display/display5.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v6/blob/main/display/display6.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v6/blob/main/display/display7.png?raw=true)
