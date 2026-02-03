BUILDINGS = [
    {"key": "imp_finger","name": "雌小鬼指尖","flavor": "一眨眼就能多戳几下，恶作剧效率大幅提升。","base_price": 10,"base_per_second": 0.5,"base_per_click": 0.5},
    {"key": "mischief_basket","name": "恶作剧小篮","flavor": "装下今日份的捉弄点子。","base_price": 80,"base_per_second": 1,"base_per_click": 0.5},
    {"key": "imp_mentor","name": "捣蛋导师","flavor": "经验丰富的雌小鬼带你加速胡闹。","base_price": 340,"base_per_second": 3,"base_per_click": 0.5},
    {"key": "imp_tree","name": "小鬼能量树","flavor": "四季都能结出“坏笑点数”。","base_price": 1500,"base_per_second": 7,"base_per_click": 1},
    {"key": "imp_garden","name": "顽皮花园","flavor": "把院子变成雌小鬼的乐园。","base_price": 6200,"base_per_second": 15,"base_per_click": 1},
    {"key": "imp_town","name": "捣蛋小镇","flavor": "所有人都参与恶作剧大合唱。","base_price": 14000,"base_per_second": 30,"base_per_click": 1.5},
    {"key": "imp_factory","name": "顽皮工坊","flavor": "自动化制造各种小坏点子。","base_price": 89000,"base_per_second": 75,"base_per_click": 1.5},
    {"key": "imp_bank","name": "恶作剧银行","flavor": "存进来的都是捣蛋计划。","base_price": 304000,"base_per_second": 110,"base_per_click": 2},
    {"key": "imp_tower","name": "雌小鬼法塔","flavor": "召唤更强的恶作剧能量。","base_price": 792000,"base_per_second": 150,"base_per_click": 2},
    {"key": "imp_ship","name": "捣蛋飞船","flavor": "跨星球搞怪也不在话下。","base_price": 1850000,"base_per_second": 250,"base_per_click": 2.5},
    {"key": "imp_wormhole","name": "小鬼虫洞","flavor": "从平行宇宙带回坏笑点数。","base_price": 4640000,"base_per_second": 400,"base_per_click": 2.5},
    {"key": "imp_time","name": "调皮时光机","flavor": "过去和未来都逃不过雌小鬼的捣乱。","base_price": 27000000,"base_per_second": 750,"base_per_click": 3},
    {"key": "imp_prism","name": "坏笑棱镜","flavor": "把光也染成恶作剧色彩。","base_price": 315000000,"base_per_second": 900,"base_per_click": 4},
    {"key": "imp_console","name": "雌小鬼控制台","flavor": "代码里也藏着捣蛋心思。","base_price": 1710000000,"base_per_second": 1200,"base_per_click": 5},
]

ACHIEVEMENTS = [
    {"key": "a1","name": "坏笑初见","rule": "累计 1 点","kind": "apples_total","threshold": 1,"reward_apples": 50,"reward_multiplier": 1.0,"reward_seconds": 0},
    {"key": "a2","name": "小坏蛋","rule": "累计 100 点","kind": "apples_total","threshold": 100,"reward_apples": 200,"reward_multiplier": 1.2,"reward_seconds": 10},
    {"key": "c1","name": "手速不错","rule": "点击 100 次","kind": "clicks","threshold": 100,"reward_apples": 300,"reward_multiplier": 1.0,"reward_seconds": 0},
    {"key": "b1","name": "第一只小鬼","rule": "拥有 1 个 雌小鬼指尖","kind": "building","threshold": 1,"building_key": "imp_finger","reward_apples": 100,"reward_multiplier": 1.1,"reward_seconds": 10},
]

UPGRADE_CARDS = [
    {"key": "card_finger","name": "指尖狂热","description": "雌小鬼指尖产出 x2","cost": 5000,"multiplier": 2.0,"target_key": "imp_finger"},
    {"key": "card_tree","name": "能量树祝福","description": "小鬼能量树产出 x2","cost": 50000,"multiplier": 2.0,"target_key": "imp_tree"},
]
