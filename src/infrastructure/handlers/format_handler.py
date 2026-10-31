class FormatHandler():
    @staticmethod
    def format_phone(phone: str) -> str:
        """Format phone as (XX) [X]XXXX-XXXX"""
        digits = ''.join(filter(str.isdigit, phone))
        
        if len(digits) == 11:
            return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
        elif len(digits) == 10:
            return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        else:
            return phone
    
    @staticmethod
    def format_zip_code(value: str) -> str:
        """Formats the zip code into Brazilian style"""
        if len(value) <= 3:
            return value
        return f"{value[:-3]}-{value[-3:]}"
