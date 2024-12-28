from sqlalchemy.orm import Session
from src.db.models.user import User
from src.schemas.user import UserCreate, UserUpdate, UserInDB

class UserCRUD:

    def get_all_user_ids(self, db: Session) -> list[str]:
        return [user.id for user in db.query(User).all()]

    def create_user(self, db: Session, user_create: UserCreate) -> UserInDB:
        new_user = User(username=user_create.username, realName=user_create.realName)
        new_user.set_password(user_create.password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return UserInDB.model_validate(new_user)

    def get_user(self, db: Session, user_id: int) -> UserInDB:
        user = db.query(User).filter(User.id == user_id).first()
        return UserInDB.model_validate(user) if user else None

    def get_user_by_username(self, db: Session, username: str) -> UserInDB:
        user = db.query(User).filter(User.username == username).first()
        return UserInDB.model_validate(user) if user else None

    def update_user(self, db: Session, user_id: int, user_update: UserUpdate) -> UserInDB:
        user = self.get_user(db, user_id)
        if not user:
            return None
        update_data = user_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return UserInDB.from_orm(user)

    def delete_user(self, db: Session, user_id: int) -> bool:
        user = self.get_user(db, user_id)
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True

    def verify_password(self, db: Session, username: str, password: str) -> bool:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False
        return user.check_password(password)