from sqlalchemy.orm import Session
from src.db.models.user_preference import UserPreference

class UserPreferenceCRUD:
    def save_user_preference(self, db: Session, user_id: int, key: str, value: str) -> UserPreference:
            # Update existing preference
        preference = db.query(UserPreference).filter(UserPreference.user_id == user_id, UserPreference.key == key).first()
        if preference:
            preference.key = key
            preference.value = value
        else:
            # Create new preference
            preference = UserPreference(user_id=user_id, key=key, value=value)
            db.add(preference)
        db.commit()
        db.refresh(preference)
        return preference

    def get_user_preferences(self, db: Session, user_id: int) -> dict[str, str]:
        preferences = db.query(UserPreference).filter(UserPreference.user_id == user_id).all()
        return {pref.key: pref.value for pref in preferences}

    def get_user_preference(self, db: Session, user_id: int, key: str) -> str | None:
        preference = db.query(UserPreference).filter(UserPreference.user_id == user_id, UserPreference.key == key).first()
        if not preference:
            return None
        return preference.value

    def delete_user_preference(self, db: Session, user_id: int, key: str) -> bool:
        preference = db.query(UserPreference).filter(UserPreference.user_id == user_id, UserPreference.key == key).first()
        if not preference:
            return False
        db.delete(preference)
        db.commit()
        return True