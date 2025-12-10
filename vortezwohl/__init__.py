__AUTHOR__ = '吴子豪 / Vortez Wohl'
__EMAIL__ = 'vortez.wohl@gmail.com'

import logging

NEW_LINE = '\n'
BLANK = ' '
UTF_8 = 'utf-8'

logger = logging.getLogger('vortezwohl')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(name)s : %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger = logging.getLogger('vortezwohl.io')
logger.setLevel(logging.INFO)
