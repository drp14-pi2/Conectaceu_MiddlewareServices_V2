import re
import bcrypt

class PasswordHasher():
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def is_bcrypt_hash(password: str) -> bool:
        """Check if string matches bcrypt format"""
        bcrypt_pattern = r'^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$'

        return bool(re.match(bcrypt_pattern, password))
