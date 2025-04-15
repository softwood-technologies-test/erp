from marketing.services.generic_services import askAI, dfToListOfDicts, updateModelWithDF
from apparelManagement.services.generic_services import applySearch, paginate

operationSections = [
        {'value': None, 'text': 'All',},
        {'value': 'SP', 'text': 'Small Parts',},
        {'value': 'B', 'text': 'Back',},
        {'value': 'F', 'text': 'Front',},
        {'value': 'A1', 'text': 'Assembly 1',},
        {'value': 'A2', 'text': 'Assembly 2',},
        {'value': 'FIN', 'text': 'Finishing',},
]

operationCategories = [
    {'value': 'Hemming', 'text': 'Hemming'},
    {'value': 'Tracing', 'text': 'Tracing'},
    {'value': 'Over Lock', 'text': 'Over Lock'},
    {'value': 'Attach', 'text': 'Attach'},
    {'value': 'Top Stitch', 'text': 'Top Stitch'},
    {'value': 'Press', 'text': 'Press'},
    {'value': 'Set Stitch', 'text': 'Set Stitch'},
    {'value': 'Safety', 'text': 'Safety'},
    {'value': 'Tacking Stitch', 'text': 'Tacking Stitch'},
    {'value': 'Feedo', 'text': 'Feedo'},
    {'value': 'Deco Stitch', 'text': 'Deco Stitch'},
    {'value': 'J Stitch', 'text': 'J Stitch'},
    {'value': 'Clipping', 'text': 'Clipping'},
    {'value': 'Turn Up', 'text': 'Turn Up'},
    {'value': 'Bartack', 'text': 'Bartack'},
    {'value': 'Eyelet', 'text': 'Eyelet'},
    {'value': 'CBE', 'text': 'CBE'},
    {'value': 'Loop', 'text': 'Loop'},
    {'value': 'Matching', 'text': 'Matching'},
    {'value': 'Mock', 'text': 'Mock'},
    {'value': 'Buffer', 'text': 'Buffer'},
]

machineTypes = [
    {'value': 'null', 'text': 'All',},
    {'value': 'SNLS', 'text': 'Single Needle Lock Stitch',},
    {'value': 'DNLS', 'text': 'Double Needle Lock Stitch',},
    {'value': 'Manu', 'text': 'Manual',},
    {'value': 'OL', 'text': 'Overlock',},
    {'value': 'SFTY', 'text': 'Safety',},
    {'value': 'Feedo', 'text': 'Feedo',},
    {'value': 'BTK', 'text': 'Bartack',},
    {'value': 'Eyelet', 'text': 'Eyelet',},
    {'value': 'WB', 'text': 'Waistband',},
    {'value': 'Loop', 'text': 'Loop Machine',},
    {'value': 'SNCS', 'text': 'Single Needle Chain Stitch',},
    {'value': 'DNCS', 'text': 'Double Needle Chain Stitch',},
    {'value': 'Buffer', 'text': 'Buffer',},
    {'value': 'AutoBone', 'text': 'Auto Bone',},
]