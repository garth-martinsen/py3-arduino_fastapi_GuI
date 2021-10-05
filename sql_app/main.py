# file:main.py

from datetime import datetime, timedelta
from typing import List, Optional
import databases
import sqlalchemy
from pydantic import BaseModel
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt

# SQLAlchemy specific code, as with any other app
DATABASE_URL = "sqlite:///./signals.db"
# DATABASE_URL = "postgresql://user:password@postgresserver/db"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

pins = sqlalchemy.Table(
    "pins",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("ts", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("src", sqlalchemy.String),
    sqlalchemy.Column("A0", sqlalchemy.Float, nullable=True),
    sqlalchemy.Column("A1", sqlalchemy.Float, nullable=True),
    sqlalchemy.Column("D2", sqlalchemy.Boolean, nullable=True),
    sqlalchemy.Column("D3", sqlalchemy.Boolean, nullable=True)
)


engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)

"""Arduino pins to save to db. Should agree with input_names in  config.py """


class PinsIn(BaseModel):
    ts: str
    src: str
    A0: int = None
    A1: int = None
    D2: bool = None
    D3: bool = None


class Pins(PinsIn):
    id: int


app = FastAPI()

#   ----------------------Security-------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "dcd0cb2848ba21dfbbb6d6769365e8bbcbbbf877eb548074ee6007584671d148"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def fake_hash_password(password: str):
    return "fakehashed" + password


fake_users_db = {
    "garth": {
        "username": "garth",
        "full_name": "Garth John Martinsen",
        "email": "garth.martinsen@gmail.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def fake_decode_token(token):
    return User(
        username=token + "fakedecoded", email="garth.martinsen@gmail.com",
        full_name="Garth John Martinsen"
    )


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(
            status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(
            status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):  # noqa: E501
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):  # noqa: E501
    user = authenticate_user(
        fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


#  --------------------------------------


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/items/")
async def read_items(token: str = Depends(oauth2_scheme)):
    return {"token": token}


@app.get("/pins", response_model=List[Pins])
async def read_pins(token: str = Depends(oauth2_scheme)):
    query = pins.select()
    return await database.fetch_all(query)


@app.post("/pins", response_model=Pins)
async def create_pins(pns: PinsIn):

    query = pins.insert().values(ts=pns.ts, src=pns.src,
                                 A0=pns.A0, A1=pns.A1,
                                 D2=pns.D2, D3=pns.D3,
                                 )

    last_record_id = await database.execute(query)

    return {**pns.dict(), "id": last_record_id}
