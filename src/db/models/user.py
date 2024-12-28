
from src.db.base_class import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
import bcrypt

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    password = Column(String)
    realName = Column(String)
     # 设置密码（自动加密）
    def set_password(self, password: str):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 验证密码
    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

User.preferences = relationship("UserPreference", back_populates="user")