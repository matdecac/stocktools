
from datetime import date, datetime, timedelta
stockList = [
    {
        'stockname': 'EUCAR.PA',
        'boughtDate': datetime.strptime('05/02/2020', '%d/%m/%Y'),
        'boughtValue': 4.16,
        'boughtQ': 6,
        'boughtFrais': 1.99,
        'sellFrais': 1.99,
    },
    {
        'stockname': 'UG.PA',
        'boughtDate': datetime.strptime('04/02/2019', '%d/%m/%Y'),
        'boughtValue': 21.99,
        'boughtQ': 1,
        'boughtFrais': 1.99,
        'sellFrais': 1.99,
    },
    {
        'stockname': 'MDM.PA',
        'boughtDate': datetime.strptime('04/11/2019', '%d/%m/%Y'),
        'boughtValue': 12.45,
        'boughtQ': 2,
        'boughtFrais': 1.99,
        'sellFrais': 1.99,
    },
    {
        'stockname': 'AKA.PA',
        'boughtDate': datetime.strptime('10/02/2020', '%d/%m/%Y'),
        'boughtValue': 55.1,
        'boughtQ': 2,
        'boughtFrais': 1.99,
        'sellFrais': 1.99,
    },
    {
        'stockname': 'SIGHT.PA',
        'boughtDate': datetime.strptime('10/02/2020', '%d/%m/%Y'),
        'boughtValue': 3.5,
        'boughtQ': 15,
        'boughtFrais': 1.99,
        'sellFrais': 1.99,
    },
]

stockArchive = [
    {
        'stockname': 'FR.PA', # VALEO
        'name': 'VALEO',
        'boughtDate': datetime.strptime('01/02/2019', '%d/%m/%Y'),
        'boughtValue': 27.30,
        'boughtQ': 1,
        'boughtFrais': 1.99,
        'sellFrais': 1.99,
        'sellTotalValue': 33.01,
        'sellValue': 35.00,
        'sellDate': datetime.strptime('28/10/2019', '%d/%m/%Y'),
    },
    {
        'stockname': 'STM.PA',
        'boughtDate': datetime.strptime('26/04/2019', '%d/%m/%Y'),
        'boughtValue': 16.20,
        'boughtQ': 1,
        'boughtFrais': 1.99,
        'sellFrais': 1.99,
        'sellTotalValue': 19.19,
        'sellValue': 21.18,
        'sellDate': datetime.strptime('06/11/2019', '%d/%m/%Y'),
    },
]


stockProspect = [
    {'stockname': 'STM.PA',},
    {'stockname': 'SO.PA',},
    {'stockname': 'AI.PA',},
    {'stockname': 'TEP.PA',},
    {'stockname': 'DBV.PA',},
    {'stockname': 'SIGHT.PA',},
    {'stockname': 'NANO.PA',},
    {'stockname': 'SAN.PA',},
    {'stockname': 'AKA.PA',},
    {'stockname': 'GNFT.PA'},
    {'stockname': 'POXEL.PA'},
    {'stockname': 'FR.PA'},
    {'stockname': 'EUCAR.PA'},
    {'stockname': 'UG.PA'},
    {'stockname': 'MDM.PA'},
]






allStocks = stockList + stockArchive