from .models import User
from .schemas import UserCreateModel
from .utils import generate_password_hash
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

class UserService: 
    async def get_user_by_username(self, username: str, session: AsyncSession):
        statement = select(User).where(User.username == username)
        
        result = await session.exec(statement)
        
        user = result.first()
        
        return user
    
    async def user_exists(self, username: str, session: AsyncSession):
        user = await self.get_user_by_username(username, session)
        
        return False if user is None else True
        
    async def create_user(self, user_data: UserCreateModel, session: AsyncSession):
        user_data_dict = user_data.model_dump()
        
        new_user = User(
            **user_data_dict  
        )
        
        new_user.password_hash = generate_password_hash(user_data_dict['password'])
        
        session.add(new_user)
        
        await session.commit()
        
        return new_user