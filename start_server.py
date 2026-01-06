import uvicorn
import os
import sys
from dotenv import load_dotenv

load_dotenv()
test_mode = os.getenv('TEST_MODE')

if __name__ == '__main__':
    if test_mode not in ['True', 'False']:
        print('TEST_MODE env variable not set properly!')
        sys.exit()
    if test_mode:
        print(f"Can't start server | test_mode: {test_mode}")
        sys.exit()
    else:
        _ = input(f'Starting server | test_mode: {test_mode}\nPress any key to Continue ')
        uvicorn.run(
            app='app.main:app', 
            host='127.0.0.1', 
            port=8000, 
            reload=True,
            reload_excludes=[
                'app/tests/conftest.py',
                'app/tests/test_root.py',
                'app/tests/test_users_router.py',
                'app/tests/test_books_router.py'
                ]
            )
        
# pydantic settings can convert common boolen values from .env file even if they are strings
# as long as the bool type hint is used
# i dont know whose worse? me or my ide
# pls dont forget single quotes in single quotes without escaping or using double quotes to wrap