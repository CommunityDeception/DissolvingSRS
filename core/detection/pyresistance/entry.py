#!/usr/bin/env python3

from core.detection.pyresistance.pyresistance import PyResistance
import os
from core.detection.pyresistance.master import logger

if __name__ == '__main__':
    data = list(os.listdir('./data'))
    for data_name in data:
        com_name = 'data/' + data_name
        logger.info(data_name)
        pyr = PyResistance.from_gml_file(com_name)
        partition, q = pyr.apply_method()
        logger.info(str(partition))
        logger.info(q)


