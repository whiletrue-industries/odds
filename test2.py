from odds.common.datatypes import Resource
from odds.backend.processor import resource_processor


if __name__ == '__main__':
    r = Resource('https://savenergyonline.stark.co.uk/government/DWP/Reports/DYTS02_kWh.csv', 'csv')
    r = resource_processor(r)

    import json
    print(json.dumps(r, ensure_ascii=False))
