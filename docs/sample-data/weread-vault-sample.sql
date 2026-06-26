BEGIN TRANSACTION;
CREATE TABLE books (
  book_id TEXT PRIMARY KEY,
  title TEXT,
  author TEXT,
  cover TEXT,
  intro TEXT,
  category TEXT,
  publish_time TEXT,
  review_count INTEGER NOT NULL DEFAULT 0,
  note_count INTEGER NOT NULL DEFAULT 0,
  bookmark_count INTEGER NOT NULL DEFAULT 0,
  total_notes INTEGER NOT NULL DEFAULT 0,
  reading_progress INTEGER,
  marked_status INTEGER,
  finished INTEGER,
  sort INTEGER,
  notes_synced_sort INTEGER,
  rating REAL,
  rating_count INTEGER,
  word_count INTEGER,
  publisher TEXT,
  isbn TEXT,
  translator TEXT,
  synced_at INTEGER NOT NULL
);
INSERT INTO "books" VALUES('sample-001','非对称风险','纳西姆·尼古拉斯·塔勒布','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-财经',NULL,0,0,0,7,100,NULL,1,10000,NULL,92.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-002','随机漫步的傻瓜','纳西姆·尼古拉斯·塔勒布','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-财经',NULL,0,0,0,12,100,NULL,1,9999,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-003','《金刚经》说什么','南怀瑾','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','哲学宗教-宗教',NULL,0,0,0,17,100,NULL,1,9998,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-004','专注的真相','李笑来','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','个人成长-励志成长',NULL,0,0,0,5,100,NULL,1,9997,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-005','许三观卖血记','余华','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','精品小说-年代小说',NULL,0,0,0,10,100,NULL,1,9996,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-006','显微镜下的大明','马伯庸','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','历史-历史读物',NULL,0,0,0,15,100,NULL,1,9995,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-007','兄弟','余华','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','精品小说-年代小说',NULL,0,0,0,3,100,NULL,1,9994,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-008','三体全集（全三册）','刘慈欣','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','精品小说-科幻小说',NULL,0,0,0,8,100,NULL,1,9993,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-009','刘慈欣三大长篇代表作（《三体》《球状闪电》《超新星纪元》）','刘慈欣','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','精品小说-科幻小说',NULL,0,0,0,13,100,NULL,1,9992,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-010','在细雨中呼喊','余华','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','精品小说-社会小说',NULL,0,0,0,18,100,NULL,1,9991,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-011','财富的真相','李笑来','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-理财',NULL,0,0,0,6,100,NULL,1,9990,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-012','Claude Code 源码解析：一份价值数十亿美元的AI工程蓝图','花叔','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','计算机-人工智能',NULL,0,0,0,11,100,NULL,1,9989,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-013','我们生活在巨大的差距里','余华','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学-散文杂著',NULL,0,0,0,16,100,NULL,1,9988,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-014','温暖和百感交集的旅程','余华','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学-经典作品',NULL,0,0,0,4,100,NULL,1,9987,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-015','走近费曼丛书：费曼讲物理：相对论','理查德·费曼','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','科学技术-自然科学',NULL,0,0,0,9,100,NULL,1,9986,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-016','走近费曼丛书·费曼讲物理：入门','理查德·费曼','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','科学技术-自然科学',NULL,0,0,0,14,100,NULL,1,9985,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-017','论语别裁（全集）','南怀瑾','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','哲学宗教-东方哲学',NULL,0,0,0,2,100,NULL,1,9984,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-018','我胆小如鼠（看完从胆小怯懦变得松弛强大！）','余华','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','精品小说-治愈小说',NULL,0,0,0,7,100,NULL,1,9983,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-019','十八岁出门远行','余华','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','精品小说-治愈小说',NULL,0,0,0,12,100,NULL,1,9982,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-020','发现的乐趣','理查德·费曼','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','人物传记-传记综合',NULL,0,0,0,17,100,NULL,1,9981,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-021','流浪地球','刘慈欣','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','精品小说-科幻小说',NULL,0,0,0,5,100,NULL,1,9980,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-022','乡村教师（电影《疯狂的外星人》原著）','刘慈欣','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','精品小说-科幻小说',NULL,0,0,0,10,100,NULL,1,9979,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-023','别再问我什么是 Loop Engineering','花叔','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','计算机-人工智能',NULL,0,0,0,15,100,NULL,1,9978,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-024','Claude Code橙皮书：从入门到精通（微信读书特别版）','花叔','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','计算机-人工智能',NULL,0,0,0,3,100,NULL,1,9977,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-025','沉默的大多数','王小波','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学-散文杂著',NULL,0,0,0,8,100,NULL,1,9976,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-026','一只特立独行的猪','王小波','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学-散文杂著',NULL,0,0,0,13,100,NULL,1,9975,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-027','把时间当作朋友（青少版修订本）','李笑来','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','个人成长-励志成长',NULL,0,0,0,18,100,NULL,1,9974,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-028','Polymarket橙皮书：预测市场完全指南','花叔','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-财经',NULL,0,0,0,6,100,NULL,1,9973,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-029','思考的真相','李笑来','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','个人成长-认知思维',NULL,0,0,0,11,100,NULL,1,9972,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-030','黄金时代','王小波','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学-经典作品',NULL,0,0,0,16,100,NULL,1,9971,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-031','文城','余华','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','精品小说-社会小说',NULL,0,0,0,4,100,NULL,1,9970,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-032','大败局（纪念版）（套装共2册）','吴晓波','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-管理',NULL,0,0,0,9,100,NULL,1,9969,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-033','激荡三十年：中国企业1978—2008（十年典藏版）（全2册）','吴晓波','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-商业',NULL,0,0,0,14,100,NULL,1,9968,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-034','腾讯传1998-2016：中国互联网公司进化论','吴晓波','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-商业',NULL,0,0,0,2,100,NULL,1,9967,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-035','易经系传别讲','南怀瑾','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','哲学宗教-东方哲学',NULL,0,0,0,7,100,NULL,1,9966,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-036','长安的荔枝（同名影视原著）','马伯庸','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','历史-历史小说',NULL,0,0,0,12,100,NULL,1,9965,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-037','风起陇西（全集）','马伯庸','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','历史-历史小说',NULL,0,0,0,17,100,NULL,1,9964,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-038','太白金星有点烦','马伯庸','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','历史-历史小说',NULL,0,0,0,5,100,NULL,1,9963,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-039','The Modern C++ Challenge','Marius Bancila','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','计算机-编程设计',NULL,0,0,0,10,71,NULL,0,9962,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-040','Modern C++ Programming Cookbook','Marius Bancila','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','计算机-编程设计',NULL,0,0,0,15,64,NULL,0,9961,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-041','肥尾效应','纳西姆·尼古拉斯·塔勒布','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-管理',NULL,0,0,0,3,57,NULL,0,9960,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-042','黑天鹅','纳西姆·尼古拉斯·塔勒布','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-财经',NULL,0,0,0,8,50,NULL,0,9959,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-043','把时间当作朋友（第4版）','李笑来','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','个人成长-人生哲学',NULL,0,0,0,0,43,NULL,0,9958,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-044','史蒂夫·乔布斯传（修订版）','沃尔特·艾萨克森','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-商业',NULL,0,0,0,0,36,NULL,0,9957,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-045','战斗细胞：人体免疫系统奇妙之旅','菲利普·德特玛','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','医学健康-医学',NULL,0,0,0,6,29,NULL,0,9956,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-046','邓小平时代','傅高义','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','未分类',NULL,0,0,0,0,22,NULL,0,9955,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-047','高效的无效：行家如何投资与市场如何定价','拉瑟·海耶·佩德森','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-财经',NULL,0,0,0,0,15,NULL,0,9954,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-048','聪明人的个人成长','史蒂夫·帕弗利纳','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','个人成长-励志成长',NULL,0,0,0,4,92,NULL,1,9953,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-049','人生十二法则：直面混乱与痛苦','乔丹·彼得森','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','心理-积极心理学',NULL,0,0,0,0,85,NULL,1,9952,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-050','埃隆·马斯克传','【美】沃尔特·艾萨克森','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','未分类',NULL,0,0,0,0,78,NULL,0,9951,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-051','原则：应对变化中的世界秩序','瑞·达利欧','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-财经',NULL,0,0,0,2,71,NULL,0,9950,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-052','杂食者的两难','迈克尔·波伦','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','生活百科-美食',NULL,0,0,0,0,64,NULL,0,9949,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-053','别对企鹅发火','[美]盖比·卡普','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','个人成长-沟通表达',NULL,0,0,0,0,57,NULL,0,9948,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-054','自在','李筱懿','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','个人成长-情绪心灵',NULL,0,0,0,17,50,NULL,0,9947,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-055','冯唐成事心法','冯唐','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-管理',NULL,0,0,0,0,43,NULL,0,9946,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-056','人性的弱点（大全集）','卡耐基','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','个人成长-沟通表达',NULL,0,0,0,0,36,NULL,0,9945,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-057','社会性动物（第12版）','艾略特·阿伦森 乔舒亚·阿伦森','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','心理-心理学研究',NULL,0,0,0,15,29,NULL,0,9944,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-058','传习录','[明]王阳明','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','哲学宗教-东方哲学',NULL,0,0,0,0,22,NULL,0,9943,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-059','中国哲学简史','冯友兰','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','哲学宗教-东方哲学',NULL,0,0,0,0,15,NULL,0,9942,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-060','CMake构建实战：项目开发卷','许宏旭','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','计算机-计算机综合',NULL,0,0,0,13,92,NULL,1,9941,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-061','世界海权博弈史','观雨者','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','历史-世界史',NULL,0,0,0,0,85,NULL,1,9940,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-062','锻炼','[美]丹尼尔·利伯曼','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','生活百科-体育',NULL,0,0,0,0,78,NULL,0,9939,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-063','自控力','凯利·麦格尼格尔','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','心理-心理学应用',NULL,0,0,0,11,71,NULL,0,9938,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-064','操作系统导论','雷姆兹·H.阿帕希杜塞尔 安德莉亚·C.阿帕希杜塞尔','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','计算机-计算机综合',NULL,0,0,0,0,64,NULL,0,9937,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-065','穷查理宝典：查理·芒格智慧箴言录（全新增订本）','彼得·考夫曼','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','个人成长-励志成长',NULL,0,0,0,0,57,NULL,0,9936,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-066','期权、期货及其他衍生产品（原书第9版）','[加]约翰·赫尔','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-理财',NULL,0,0,0,9,50,NULL,0,9935,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-067','打开心智','李睿秋','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','个人成长-认知思维',NULL,0,0,0,0,43,NULL,0,9934,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-068','非暴力沟通（修订版）','马歇尔·卢森堡','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','心理-心理学应用',NULL,0,0,0,0,36,NULL,0,9933,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-069','李敖电子书大全集[34本合集]','李敖','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','未分类',NULL,0,0,0,7,29,NULL,0,9932,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-070','瓦尔登湖（译文经典）','梭罗','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学-散文杂著',NULL,0,0,0,0,22,NULL,0,9931,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-071','被讨厌的勇气：“自我启发之父”阿德勒的哲学课','岸见一郎 古贺史健','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','心理-积极心理学',NULL,0,0,0,0,15,NULL,0,9930,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-072','曾医生让你早知道','普外科曾医生','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','医学健康-健康',NULL,0,0,0,5,92,NULL,1,9929,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-073','置身事内：中国政府与经济发展','兰小欢','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-财经',NULL,0,0,0,0,85,NULL,1,9928,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-074','与塞涅卡共进早餐：斯多葛哲学的人生艺术','大卫·菲德勒','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','哲学宗教-西方哲学',NULL,0,0,0,0,78,NULL,0,9927,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-075','硅谷之火：个人计算机的诞生与衰落（第3版）','迈克尔·斯韦因 保罗·弗赖伯格','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','计算机-计算机综合',NULL,0,0,0,3,71,NULL,0,9926,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-076','看见','柴静','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学-散文杂著',NULL,0,0,0,0,64,NULL,0,9925,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-077','轻松主义：让关键的事情变得容易做','[美]格雷戈·麦吉沃恩','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','个人成长-人生哲学',NULL,0,0,0,0,57,NULL,0,9924,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-078','癌症病人怎么吃？（译文科学）','王兴','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','医学健康-健康',NULL,0,0,0,18,50,NULL,0,9923,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-079','现代C++编程：从入门到实践','乔什·洛斯皮诺索','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','计算机-编程设计',NULL,0,0,0,0,43,NULL,0,9922,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-080','重塑杏仁核：情绪修复脑科学','[美]凯瑟琳·M. 皮特曼','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','心理-心理学研究',NULL,0,0,0,0,36,NULL,0,9921,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-081','青年变革者：梁启超（1873—1898）','许知远','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','历史-中国近现代',NULL,0,0,0,16,29,NULL,0,9920,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-082','未来简史：从智人到智神','尤瓦尔·赫拉利','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','社会文化-社科',NULL,0,0,0,0,22,NULL,0,9919,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-083','认识世界：古代与中世纪哲学','理查德·大卫·普莱希特','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','哲学宗教-哲学读物',NULL,0,0,0,0,15,NULL,0,9918,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-084','了凡四训','[明]袁了凡','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','哲学宗教-东方哲学',NULL,0,0,0,14,92,NULL,1,9917,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-085','梁永安：阅读、游历和爱情','梁永安','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学-散文杂著',NULL,0,0,0,0,85,NULL,1,9916,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-086','轻断食：正在横扫全球的瘦身革命','麦克尔·莫斯利 咪咪·史宾赛','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','医学健康-健康',NULL,0,0,0,0,78,NULL,0,9915,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-087','3小时快学期权（第二版）','上海证券交易所产品创新中心','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-财经',NULL,0,0,0,12,71,NULL,0,9914,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-088','做一个清醒的现代人','刘擎','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学-散文杂著',NULL,0,0,0,0,64,NULL,0,9913,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-089','王阳明心学入门三步走（全三册）','度阴山','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','哲学宗教-东方哲学',NULL,0,0,0,0,57,NULL,0,9912,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-090','技术的本质（经典版）','布莱恩·阿瑟','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','科学技术-自然科学',NULL,0,0,0,10,50,NULL,0,9911,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-091','人人都懂设计模式：从生活中领悟设计模式（Python实现）','罗伟富','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','计算机-编程设计',NULL,0,0,0,0,43,NULL,0,9910,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-092','我的阿勒泰（马伊琍、周依然、于适主演同名电视剧原著）','李娟','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','精品小说-影视原著',NULL,0,0,0,0,36,NULL,0,9909,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-093','存在主义咖啡馆：自由、存在和杏子鸡尾酒','莎拉·贝克韦尔','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','哲学宗教-哲学读物',NULL,0,0,0,8,29,NULL,0,9908,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-094','习惯逃避：你在害怕什么（回避型人格自救手册。拖延、讨好、自卑、社恐的背后，不过是一颗习惯逃避的灵魂。）','李国翠','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','心理-认知与行为',NULL,0,0,0,0,22,NULL,0,9907,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-095','职场高效阅读：成为高手的实用阅读秘籍','朱晓华','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','个人成长-认知思维',NULL,0,0,0,0,15,NULL,0,9906,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-096','原则：绘本版(汉英对照)','瑞·达利欧','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','教育学习-育儿',NULL,0,0,0,6,92,NULL,1,9905,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-097','复利：全球顶尖投资者的31节认知与决策思维课','[美]高塔姆·拜德','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','经济理财-理财',NULL,0,0,0,0,85,NULL,1,9904,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-098','乡村医生','弗兰茨·卡夫卡','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学-经典作品',NULL,0,0,0,0,78,NULL,0,9903,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-099','现代C++语言核心特性解析','谢丙堃','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','计算机-编程设计',NULL,0,0,0,4,71,NULL,0,9902,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-100','好好恋爱','安德鲁·G.马歇尔','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','生活百科-情感',NULL,0,0,0,0,64,NULL,0,9901,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
CREATE TABLE highlights (
  bookmark_id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
  chapter_uid INTEGER,
  chapter_title TEXT,
  mark_text TEXT,
  text_range TEXT,
  color_style INTEGER,
  create_time INTEGER,
  updated_at INTEGER NOT NULL
);
INSERT INTO "highlights" VALUES('sample-highlight-1','sample-001',1,'序章 为什么要保存阅读现场','真正重要的不是读过多少，而是那些被你反复想起的句子。','100-120',5,1780243200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-2','sample-001',2,'第一章 本地优先','把数据放回自己手里，工具才会变成长期可依赖的基础设施。','200-220',4,1780416000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-3','sample-001',3,'第二章 搜索与回看','笔记的价值常常在第二次相遇时出现。','300-320',3,1780502400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-4','sample-001',4,'第三章 与 AI 协作','让 agent 读取结构化笔记，而不是让记忆散落在聊天记录里。','400-420',5,1780588800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-5','sample-002',1,'第 1 章','这是一条围绕《随机漫步的傻瓜》生成的虚构示例划线，用来演示本地检索和统计。','100-120',3,1780347600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-6','sample-002',2,'第 2 章','这是一条围绕《随机漫步的傻瓜》生成的虚构示例划线，用来演示本地检索和统计。','200-220',4,1780354800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-7','sample-002',3,'第 3 章','这是一条围绕《随机漫步的傻瓜》生成的虚构示例划线，用来演示本地检索和统计。','300-320',5,1780362000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-8','sample-003',1,'第 1 章','这是一条围绕《《金刚经》说什么》生成的虚构示例划线，用来演示本地检索和统计。','100-120',4,1780444800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-9','sample-003',2,'第 2 章','这是一条围绕《《金刚经》说什么》生成的虚构示例划线，用来演示本地检索和统计。','200-220',5,1780452000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-10','sample-003',3,'第 3 章','这是一条围绕《《金刚经》说什么》生成的虚构示例划线，用来演示本地检索和统计。','300-320',1,1780459200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-11','sample-004',1,'第 1 章','这是一条围绕《专注的真相》生成的虚构示例划线，用来演示本地检索和统计。','100-120',5,1780542000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-12','sample-005',1,'第 1 章','这是一条围绕《许三观卖血记》生成的虚构示例划线，用来演示本地检索和统计。','100-120',1,1780639200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-13','sample-005',2,'第 2 章','这是一条围绕《许三观卖血记》生成的虚构示例划线，用来演示本地检索和统计。','200-220',2,1780646400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-14','sample-006',1,'第 1 章','这是一条围绕《显微镜下的大明》生成的虚构示例划线，用来演示本地检索和统计。','100-120',2,1780736400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-15','sample-006',2,'第 2 章','这是一条围绕《显微镜下的大明》生成的虚构示例划线，用来演示本地检索和统计。','200-220',3,1780743600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-16','sample-006',3,'第 3 章','这是一条围绕《显微镜下的大明》生成的虚构示例划线，用来演示本地检索和统计。','300-320',4,1780750800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-17','sample-007',1,'第 1 章','这是一条围绕《兄弟》生成的虚构示例划线，用来演示本地检索和统计。','100-120',3,1780833600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-18','sample-008',1,'第 1 章','这是一条围绕《三体全集（全三册）》生成的虚构示例划线，用来演示本地检索和统计。','100-120',4,1780930800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-19','sample-008',2,'第 2 章','这是一条围绕《三体全集（全三册）》生成的虚构示例划线，用来演示本地检索和统计。','200-220',5,1780851600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-20','sample-009',1,'第 1 章','这是一条围绕《刘慈欣三大长篇代表作（《三体》《球状闪电》《超新星纪元》）》生成的虚构示例划线，用来演示本地检索和统计。','100-120',5,1780941600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-21','sample-009',2,'第 2 章','这是一条围绕《刘慈欣三大长篇代表作（《三体》《球状闪电》《超新星纪元》）》生成的虚构示例划线，用来演示本地检索和统计。','200-220',1,1780948800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-22','sample-009',3,'第 3 章','这是一条围绕《刘慈欣三大长篇代表作（《三体》《球状闪电》《超新星纪元》）》生成的虚构示例划线，用来演示本地检索和统计。','300-320',2,1780956000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-23','sample-010',1,'第 1 章','这是一条围绕《在细雨中呼喊》生成的虚构示例划线，用来演示本地检索和统计。','100-120',1,1781038800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-24','sample-010',2,'第 2 章','这是一条围绕《在细雨中呼喊》生成的虚构示例划线，用来演示本地检索和统计。','200-220',2,1781046000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-25','sample-010',3,'第 3 章','这是一条围绕《在细雨中呼喊》生成的虚构示例划线，用来演示本地检索和统计。','300-320',3,1781053200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-26','sample-011',1,'第 1 章','这是一条围绕《财富的真相》生成的虚构示例划线，用来演示本地检索和统计。','100-120',2,1781136000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-27','sample-011',2,'第 2 章','这是一条围绕《财富的真相》生成的虚构示例划线，用来演示本地检索和统计。','200-220',3,1781143200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-28','sample-012',1,'第 1 章','这是一条围绕《Claude Code 源码解析：一份价值数十亿美元的AI工程蓝图》生成的虚构示例划线，用来演示本地检索和统计。','100-120',3,1781233200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-29','sample-012',2,'第 2 章','这是一条围绕《Claude Code 源码解析：一份价值数十亿美元的AI工程蓝图》生成的虚构示例划线，用来演示本地检索和统计。','200-220',4,1781240400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-30','sample-013',1,'第 1 章','这是一条围绕《我们生活在巨大的差距里》生成的虚构示例划线，用来演示本地检索和统计。','100-120',4,1781330400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-31','sample-013',2,'第 2 章','这是一条围绕《我们生活在巨大的差距里》生成的虚构示例划线，用来演示本地检索和统计。','200-220',5,1781337600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-32','sample-013',3,'第 3 章','这是一条围绕《我们生活在巨大的差距里》生成的虚构示例划线，用来演示本地检索和统计。','300-320',1,1781344800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-33','sample-014',1,'第 1 章','这是一条围绕《温暖和百感交集的旅程》生成的虚构示例划线，用来演示本地检索和统计。','100-120',5,1781427600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-34','sample-015',1,'第 1 章','这是一条围绕《走近费曼丛书：费曼讲物理：相对论》生成的虚构示例划线，用来演示本地检索和统计。','100-120',1,1781524800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-35','sample-015',2,'第 2 章','这是一条围绕《走近费曼丛书：费曼讲物理：相对论》生成的虚构示例划线，用来演示本地检索和统计。','200-220',2,1781532000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-36','sample-016',1,'第 1 章','这是一条围绕《走近费曼丛书·费曼讲物理：入门》生成的虚构示例划线，用来演示本地检索和统计。','100-120',2,1781622000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-37','sample-016',2,'第 2 章','这是一条围绕《走近费曼丛书·费曼讲物理：入门》生成的虚构示例划线，用来演示本地检索和统计。','200-220',3,1781542800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-38','sample-016',3,'第 3 章','这是一条围绕《走近费曼丛书·费曼讲物理：入门》生成的虚构示例划线，用来演示本地检索和统计。','300-320',4,1781550000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-39','sample-017',1,'第 1 章','这是一条围绕《论语别裁（全集）》生成的虚构示例划线，用来演示本地检索和统计。','100-120',3,1781632800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-40','sample-018',1,'第 1 章','这是一条围绕《我胆小如鼠（看完从胆小怯懦变得松弛强大！）》生成的虚构示例划线，用来演示本地检索和统计。','100-120',4,1781730000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-41','sample-018',2,'第 2 章','这是一条围绕《我胆小如鼠（看完从胆小怯懦变得松弛强大！）》生成的虚构示例划线，用来演示本地检索和统计。','200-220',5,1781737200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-42','sample-019',1,'第 1 章','这是一条围绕《十八岁出门远行》生成的虚构示例划线，用来演示本地检索和统计。','100-120',5,1781827200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-43','sample-019',2,'第 2 章','这是一条围绕《十八岁出门远行》生成的虚构示例划线，用来演示本地检索和统计。','200-220',1,1781834400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-44','sample-019',3,'第 3 章','这是一条围绕《十八岁出门远行》生成的虚构示例划线，用来演示本地检索和统计。','300-320',2,1781841600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-45','sample-020',1,'第 1 章','这是一条围绕《发现的乐趣》生成的虚构示例划线，用来演示本地检索和统计。','100-120',1,1781924400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-46','sample-020',2,'第 2 章','这是一条围绕《发现的乐趣》生成的虚构示例划线，用来演示本地检索和统计。','200-220',2,1781931600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-47','sample-020',3,'第 3 章','这是一条围绕《发现的乐趣》生成的虚构示例划线，用来演示本地检索和统计。','300-320',3,1781938800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-48','sample-021',1,'第 1 章','这是一条围绕《流浪地球》生成的虚构示例划线，用来演示本地检索和统计。','100-120',2,1782021600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-49','sample-022',1,'第 1 章','这是一条围绕《乡村教师（电影《疯狂的外星人》原著）》生成的虚构示例划线，用来演示本地检索和统计。','100-120',3,1780304400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-50','sample-022',2,'第 2 章','这是一条围绕《乡村教师（电影《疯狂的外星人》原著）》生成的虚构示例划线，用来演示本地检索和统计。','200-220',4,1780311600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-51','sample-023',1,'第 1 章','这是一条围绕《别再问我什么是 Loop Engineering》生成的虚构示例划线，用来演示本地检索和统计。','100-120',4,1780401600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-52','sample-023',2,'第 2 章','这是一条围绕《别再问我什么是 Loop Engineering》生成的虚构示例划线，用来演示本地检索和统计。','200-220',5,1780408800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-53','sample-023',3,'第 3 章','这是一条围绕《别再问我什么是 Loop Engineering》生成的虚构示例划线，用来演示本地检索和统计。','300-320',1,1780329600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-54','sample-024',1,'第 1 章','这是一条围绕《Claude Code橙皮书：从入门到精通（微信读书特别版）》生成的虚构示例划线，用来演示本地检索和统计。','100-120',5,1780498800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-55','sample-025',1,'第 1 章','这是一条围绕《沉默的大多数》生成的虚构示例划线，用来演示本地检索和统计。','100-120',1,1780509600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-56','sample-025',2,'第 2 章','这是一条围绕《沉默的大多数》生成的虚构示例划线，用来演示本地检索和统计。','200-220',2,1780516800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-57','sample-026',1,'第 1 章','这是一条围绕《一只特立独行的猪》生成的虚构示例划线，用来演示本地检索和统计。','100-120',2,1780606800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-58','sample-026',2,'第 2 章','这是一条围绕《一只特立独行的猪》生成的虚构示例划线，用来演示本地检索和统计。','200-220',3,1780614000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-59','sample-026',3,'第 3 章','这是一条围绕《一只特立独行的猪》生成的虚构示例划线，用来演示本地检索和统计。','300-320',4,1780621200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-60','sample-027',1,'第 1 章','这是一条围绕《把时间当作朋友（青少版修订本）》生成的虚构示例划线，用来演示本地检索和统计。','100-120',3,1780704000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-61','sample-027',2,'第 2 章','这是一条围绕《把时间当作朋友（青少版修订本）》生成的虚构示例划线，用来演示本地检索和统计。','200-220',4,1780711200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-62','sample-027',3,'第 3 章','这是一条围绕《把时间当作朋友（青少版修订本）》生成的虚构示例划线，用来演示本地检索和统计。','300-320',5,1780718400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-63','sample-028',1,'第 1 章','这是一条围绕《Polymarket橙皮书：预测市场完全指南》生成的虚构示例划线，用来演示本地检索和统计。','100-120',4,1780801200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-64','sample-028',2,'第 2 章','这是一条围绕《Polymarket橙皮书：预测市场完全指南》生成的虚构示例划线，用来演示本地检索和统计。','200-220',5,1780808400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-65','sample-029',1,'第 1 章','这是一条围绕《思考的真相》生成的虚构示例划线，用来演示本地检索和统计。','100-120',5,1780898400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-66','sample-029',2,'第 2 章','这是一条围绕《思考的真相》生成的虚构示例划线，用来演示本地检索和统计。','200-220',1,1780905600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-67','sample-030',1,'第 1 章','这是一条围绕《黄金时代》生成的虚构示例划线，用来演示本地检索和统计。','100-120',1,1780995600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-68','sample-030',2,'第 2 章','这是一条围绕《黄金时代》生成的虚构示例划线，用来演示本地检索和统计。','200-220',2,1781002800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-69','sample-030',3,'第 3 章','这是一条围绕《黄金时代》生成的虚构示例划线，用来演示本地检索和统计。','300-320',3,1781010000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-70','sample-031',1,'第 1 章','这是一条围绕《文城》生成的虚构示例划线，用来演示本地检索和统计。','100-120',2,1781092800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-71','sample-032',1,'第 1 章','这是一条围绕《大败局（纪念版）（套装共2册）》生成的虚构示例划线，用来演示本地检索和统计。','100-120',3,1781190000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-72','sample-032',2,'第 2 章','这是一条围绕《大败局（纪念版）（套装共2册）》生成的虚构示例划线，用来演示本地检索和统计。','200-220',4,1781110800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-73','sample-033',1,'第 1 章','这是一条围绕《激荡三十年：中国企业1978—2008（十年典藏版）（全2册）》生成的虚构示例划线，用来演示本地检索和统计。','100-120',4,1781200800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-74','sample-033',2,'第 2 章','这是一条围绕《激荡三十年：中国企业1978—2008（十年典藏版）（全2册）》生成的虚构示例划线，用来演示本地检索和统计。','200-220',5,1781208000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-75','sample-033',3,'第 3 章','这是一条围绕《激荡三十年：中国企业1978—2008（十年典藏版）（全2册）》生成的虚构示例划线，用来演示本地检索和统计。','300-320',1,1781215200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-76','sample-034',1,'第 1 章','这是一条围绕《腾讯传1998-2016：中国互联网公司进化论》生成的虚构示例划线，用来演示本地检索和统计。','100-120',5,1781298000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-77','sample-035',1,'第 1 章','这是一条围绕《易经系传别讲》生成的虚构示例划线，用来演示本地检索和统计。','100-120',1,1781395200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-78','sample-035',2,'第 2 章','这是一条围绕《易经系传别讲》生成的虚构示例划线，用来演示本地检索和统计。','200-220',2,1781402400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-79','sample-036',1,'第 1 章','这是一条围绕《长安的荔枝（同名影视原著）》生成的虚构示例划线，用来演示本地检索和统计。','100-120',2,1781492400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-80','sample-036',2,'第 2 章','这是一条围绕《长安的荔枝（同名影视原著）》生成的虚构示例划线，用来演示本地检索和统计。','200-220',3,1781499600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-81','sample-036',3,'第 3 章','这是一条围绕《长安的荔枝（同名影视原著）》生成的虚构示例划线，用来演示本地检索和统计。','300-320',4,1781506800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-82','sample-037',1,'第 1 章','这是一条围绕《风起陇西（全集）》生成的虚构示例划线，用来演示本地检索和统计。','100-120',3,1781589600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-83','sample-037',2,'第 2 章','这是一条围绕《风起陇西（全集）》生成的虚构示例划线，用来演示本地检索和统计。','200-220',4,1781596800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-84','sample-037',3,'第 3 章','这是一条围绕《风起陇西（全集）》生成的虚构示例划线，用来演示本地检索和统计。','300-320',5,1781604000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-85','sample-038',1,'第 1 章','这是一条围绕《太白金星有点烦》生成的虚构示例划线，用来演示本地检索和统计。','100-120',4,1781686800,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-86','sample-039',1,'第 1 章','这是一条围绕《The Modern C++ Challenge》生成的虚构示例划线，用来演示本地检索和统计。','100-120',5,1781784000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-87','sample-039',2,'第 2 章','这是一条围绕《The Modern C++ Challenge》生成的虚构示例划线，用来演示本地检索和统计。','200-220',1,1781791200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-88','sample-040',1,'第 1 章','这是一条围绕《Modern C++ Programming Cookbook》生成的虚构示例划线，用来演示本地检索和统计。','100-120',1,1781881200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-89','sample-040',2,'第 2 章','这是一条围绕《Modern C++ Programming Cookbook》生成的虚构示例划线，用来演示本地检索和统计。','200-220',2,1781802000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-90','sample-040',3,'第 3 章','这是一条围绕《Modern C++ Programming Cookbook》生成的虚构示例划线，用来演示本地检索和统计。','300-320',3,1781809200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-91','sample-041',1,'第 1 章','这是一条围绕《肥尾效应》生成的虚构示例划线，用来演示本地检索和统计。','100-120',2,1781892000,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-92','sample-042',1,'第 1 章','这是一条围绕《黑天鹅》生成的虚构示例划线，用来演示本地检索和统计。','100-120',3,1781989200,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-93','sample-042',2,'第 2 章','这是一条围绕《黑天鹅》生成的虚构示例划线，用来演示本地检索和统计。','200-220',4,1781996400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-94','sample-045',1,'第 1 章','这是一条围绕《战斗细胞：人体免疫系统奇妙之旅》生成的虚构示例划线，用来演示本地检索和统计。','100-120',1,1780466400,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-95','sample-045',2,'第 2 章','这是一条围绕《战斗细胞：人体免疫系统奇妙之旅》生成的虚构示例划线，用来演示本地检索和统计。','200-220',2,1780473600,1782403200);
INSERT INTO "highlights" VALUES('sample-highlight-96','sample-048',1,'第 1 章','这是一条围绕《聪明人的个人成长》生成的虚构示例划线，用来演示本地检索和统计。','100-120',4,1780758000,1782403200);
CREATE TABLE popular_highlights (
  book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
  chapter_uid INTEGER,
  chapter_title TEXT,
  mark_text TEXT,
  text_range TEXT,
  count INTEGER,
  synced_at INTEGER NOT NULL,
  PRIMARY KEY (book_id, text_range)
);
INSERT INTO "popular_highlights" VALUES('sample-001',1,'序章 为什么要保存阅读现场','当阅读记录可以被检索，过去的自己就会变成一个安静的协作者。','1000-1001',284,1782403200);
INSERT INTO "popular_highlights" VALUES('sample-001',2,'第一章 本地优先','本地数据库的意义，是让私人知识不必为了便利而失去边界。','2000-2002',197,1782403200);
INSERT INTO "popular_highlights" VALUES('sample-001',3,'第二章 搜索与回看','好的归档不是收藏，而是在需要时把线索送回眼前。','3000-3003',163,1782403200);
INSERT INTO "popular_highlights" VALUES('sample-001',4,'第三章 与 AI 协作','AI 读结构化数据时，回答会少一点猜测，多一点证据。','4000-4004',121,1782403200);
CREATE TABLE reading_stats (
  id INTEGER PRIMARY KEY,
  mode TEXT NOT NULL,
  base_time INTEGER NOT NULL DEFAULT 0,
  payload TEXT NOT NULL,
  fetched_at INTEGER NOT NULL
);
INSERT INTO "reading_stats" VALUES(1,'overall',0,'{"totalReadTime": 216000, "readDays": 64, "readTimes": {"1735660800": 64800, "1767196800": 88200}, "readLongest": [{"book": {"title": "非对称风险", "author": "纳西姆·尼古拉斯·塔勒布"}, "readTime": 7800}, {"book": {"title": "随机漫步的傻瓜", "author": "纳西姆·尼古拉斯·塔勒布"}, "readTime": 7180}, {"book": {"title": "《金刚经》说什么", "author": "南怀瑾"}, "readTime": 6560}, {"book": {"title": "专注的真相", "author": "李笑来"}, "readTime": 5940}, {"book": {"title": "许三观卖血记", "author": "余华"}, "readTime": 5320}, {"book": {"title": "显微镜下的大明", "author": "马伯庸"}, "readTime": 4700}, {"book": {"title": "兄弟", "author": "余华"}, "readTime": 4080}, {"book": {"title": "三体全集（全三册）", "author": "刘慈欣"}, "readTime": 3460}], "preferCategory": [{"categoryTitle": "经济理财-财经", "readingTime": 16200, "readingCount": 6}, {"categoryTitle": "精品小说-科幻小说", "readingTime": 12000, "readingCount": 4}, {"categoryTitle": "个人成长-励志成长", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "历史-历史小说", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "哲学宗教-东方哲学", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "文学-散文杂著", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "科学技术-自然科学", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "计算机-人工智能", "readingTime": 9900, "readingCount": 3}], "preferAuthor": [{"name": "余华", "count": 8, "readTime": "8 次"}, {"name": "刘慈欣", "count": 4, "readTime": "4 次"}, {"name": "李笑来", "count": 4, "readTime": "4 次"}, {"name": "纳西姆·尼古拉斯·塔勒布", "count": 4, "readTime": "4 次"}, {"name": "花叔", "count": 4, "readTime": "4 次"}, {"name": "马伯庸", "count": 4, "readTime": "4 次"}, {"name": "南怀瑾", "count": 3, "readTime": "3 次"}, {"name": "吴晓波", "count": 3, "readTime": "3 次"}], "preferTime": [0, 0, 0, 0, 0, 0, 1, 3, 5, 4, 3, 2, 2, 4, 6, 8, 7, 5, 4, 3, 2, 1, 0, 0], "readStat": [{"stat": "读过", "counts": "100本"}], "preferCategoryWord": "经济理财-财经", "preferTimeWord": "傍晚阅读较多"}',1782403200);
INSERT INTO "reading_stats" VALUES(2,'annually',0,'{"totalReadTime": 216000, "readDays": 64, "readTimes": {"1735660800": 64800, "1767196800": 88200}, "readLongest": [{"book": {"title": "非对称风险", "author": "纳西姆·尼古拉斯·塔勒布"}, "readTime": 7800}, {"book": {"title": "随机漫步的傻瓜", "author": "纳西姆·尼古拉斯·塔勒布"}, "readTime": 7180}, {"book": {"title": "《金刚经》说什么", "author": "南怀瑾"}, "readTime": 6560}, {"book": {"title": "专注的真相", "author": "李笑来"}, "readTime": 5940}, {"book": {"title": "许三观卖血记", "author": "余华"}, "readTime": 5320}, {"book": {"title": "显微镜下的大明", "author": "马伯庸"}, "readTime": 4700}, {"book": {"title": "兄弟", "author": "余华"}, "readTime": 4080}, {"book": {"title": "三体全集（全三册）", "author": "刘慈欣"}, "readTime": 3460}], "preferCategory": [{"categoryTitle": "经济理财-财经", "readingTime": 16200, "readingCount": 6}, {"categoryTitle": "精品小说-科幻小说", "readingTime": 12000, "readingCount": 4}, {"categoryTitle": "个人成长-励志成长", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "历史-历史小说", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "哲学宗教-东方哲学", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "文学-散文杂著", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "科学技术-自然科学", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "计算机-人工智能", "readingTime": 9900, "readingCount": 3}], "preferAuthor": [{"name": "余华", "count": 8, "readTime": "8 次"}, {"name": "刘慈欣", "count": 4, "readTime": "4 次"}, {"name": "李笑来", "count": 4, "readTime": "4 次"}, {"name": "纳西姆·尼古拉斯·塔勒布", "count": 4, "readTime": "4 次"}, {"name": "花叔", "count": 4, "readTime": "4 次"}, {"name": "马伯庸", "count": 4, "readTime": "4 次"}, {"name": "南怀瑾", "count": 3, "readTime": "3 次"}, {"name": "吴晓波", "count": 3, "readTime": "3 次"}], "preferTime": [0, 0, 0, 0, 0, 0, 1, 3, 5, 4, 3, 2, 2, 4, 6, 8, 7, 5, 4, 3, 2, 1, 0, 0], "readStat": [{"stat": "读过", "counts": "100本"}], "preferCategoryWord": "经济理财-财经", "preferTimeWord": "傍晚阅读较多"}',1782403200);
INSERT INTO "reading_stats" VALUES(3,'monthly',0,'{"totalReadTime": 216000, "readDays": 64, "readTimes": {"1735660800": 64800, "1767196800": 88200}, "readLongest": [{"book": {"title": "非对称风险", "author": "纳西姆·尼古拉斯·塔勒布"}, "readTime": 7800}, {"book": {"title": "随机漫步的傻瓜", "author": "纳西姆·尼古拉斯·塔勒布"}, "readTime": 7180}, {"book": {"title": "《金刚经》说什么", "author": "南怀瑾"}, "readTime": 6560}, {"book": {"title": "专注的真相", "author": "李笑来"}, "readTime": 5940}, {"book": {"title": "许三观卖血记", "author": "余华"}, "readTime": 5320}, {"book": {"title": "显微镜下的大明", "author": "马伯庸"}, "readTime": 4700}, {"book": {"title": "兄弟", "author": "余华"}, "readTime": 4080}, {"book": {"title": "三体全集（全三册）", "author": "刘慈欣"}, "readTime": 3460}], "preferCategory": [{"categoryTitle": "经济理财-财经", "readingTime": 16200, "readingCount": 6}, {"categoryTitle": "精品小说-科幻小说", "readingTime": 12000, "readingCount": 4}, {"categoryTitle": "个人成长-励志成长", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "历史-历史小说", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "哲学宗教-东方哲学", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "文学-散文杂著", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "科学技术-自然科学", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "计算机-人工智能", "readingTime": 9900, "readingCount": 3}], "preferAuthor": [{"name": "余华", "count": 8, "readTime": "8 次"}, {"name": "刘慈欣", "count": 4, "readTime": "4 次"}, {"name": "李笑来", "count": 4, "readTime": "4 次"}, {"name": "纳西姆·尼古拉斯·塔勒布", "count": 4, "readTime": "4 次"}, {"name": "花叔", "count": 4, "readTime": "4 次"}, {"name": "马伯庸", "count": 4, "readTime": "4 次"}, {"name": "南怀瑾", "count": 3, "readTime": "3 次"}, {"name": "吴晓波", "count": 3, "readTime": "3 次"}], "preferTime": [0, 0, 0, 0, 0, 0, 1, 3, 5, 4, 3, 2, 2, 4, 6, 8, 7, 5, 4, 3, 2, 1, 0, 0], "readStat": [{"stat": "读过", "counts": "100本"}], "preferCategoryWord": "经济理财-财经", "preferTimeWord": "傍晚阅读较多"}',1782403200);
INSERT INTO "reading_stats" VALUES(4,'weekly',0,'{"totalReadTime": 216000, "readDays": 64, "readTimes": {"1735660800": 64800, "1767196800": 88200}, "readLongest": [{"book": {"title": "非对称风险", "author": "纳西姆·尼古拉斯·塔勒布"}, "readTime": 7800}, {"book": {"title": "随机漫步的傻瓜", "author": "纳西姆·尼古拉斯·塔勒布"}, "readTime": 7180}, {"book": {"title": "《金刚经》说什么", "author": "南怀瑾"}, "readTime": 6560}, {"book": {"title": "专注的真相", "author": "李笑来"}, "readTime": 5940}, {"book": {"title": "许三观卖血记", "author": "余华"}, "readTime": 5320}, {"book": {"title": "显微镜下的大明", "author": "马伯庸"}, "readTime": 4700}, {"book": {"title": "兄弟", "author": "余华"}, "readTime": 4080}, {"book": {"title": "三体全集（全三册）", "author": "刘慈欣"}, "readTime": 3460}], "preferCategory": [{"categoryTitle": "经济理财-财经", "readingTime": 16200, "readingCount": 6}, {"categoryTitle": "精品小说-科幻小说", "readingTime": 12000, "readingCount": 4}, {"categoryTitle": "个人成长-励志成长", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "历史-历史小说", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "哲学宗教-东方哲学", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "文学-散文杂著", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "科学技术-自然科学", "readingTime": 9900, "readingCount": 3}, {"categoryTitle": "计算机-人工智能", "readingTime": 9900, "readingCount": 3}], "preferAuthor": [{"name": "余华", "count": 8, "readTime": "8 次"}, {"name": "刘慈欣", "count": 4, "readTime": "4 次"}, {"name": "李笑来", "count": 4, "readTime": "4 次"}, {"name": "纳西姆·尼古拉斯·塔勒布", "count": 4, "readTime": "4 次"}, {"name": "花叔", "count": 4, "readTime": "4 次"}, {"name": "马伯庸", "count": 4, "readTime": "4 次"}, {"name": "南怀瑾", "count": 3, "readTime": "3 次"}, {"name": "吴晓波", "count": 3, "readTime": "3 次"}], "preferTime": [0, 0, 0, 0, 0, 0, 1, 3, 5, 4, 3, 2, 2, 4, 6, 8, 7, 5, 4, 3, 2, 1, 0, 0], "readStat": [{"stat": "读过", "counts": "100本"}], "preferCategoryWord": "经济理财-财经", "preferTimeWord": "傍晚阅读较多"}',1782403200);
CREATE TABLE sample_book_styles (
              book_id TEXT PRIMARY KEY,
              color1 TEXT NOT NULL,
              color2 TEXT NOT NULL
            );
INSERT INTO "sample_book_styles" VALUES('sample-001','#2563eb','#7c3aed');
INSERT INTO "sample_book_styles" VALUES('sample-002','#059669','#14b8a6');
INSERT INTO "sample_book_styles" VALUES('sample-003','#dc2626','#f97316');
INSERT INTO "sample_book_styles" VALUES('sample-004','#9333ea','#ec4899');
INSERT INTO "sample_book_styles" VALUES('sample-005','#0f766e','#65a30d');
INSERT INTO "sample_book_styles" VALUES('sample-006','#0369a1','#38bdf8');
INSERT INTO "sample_book_styles" VALUES('sample-007','#ca8a04','#f59e0b');
INSERT INTO "sample_book_styles" VALUES('sample-008','#db2777','#fb7185');
INSERT INTO "sample_book_styles" VALUES('sample-009','#4f46e5','#06b6d4');
INSERT INTO "sample_book_styles" VALUES('sample-010','#475569','#64748b');
INSERT INTO "sample_book_styles" VALUES('sample-011','#ea580c','#facc15');
INSERT INTO "sample_book_styles" VALUES('sample-012','#16a34a','#84cc16');
INSERT INTO "sample_book_styles" VALUES('sample-013','#2563eb','#7c3aed');
INSERT INTO "sample_book_styles" VALUES('sample-014','#059669','#14b8a6');
INSERT INTO "sample_book_styles" VALUES('sample-015','#dc2626','#f97316');
INSERT INTO "sample_book_styles" VALUES('sample-016','#9333ea','#ec4899');
INSERT INTO "sample_book_styles" VALUES('sample-017','#0f766e','#65a30d');
INSERT INTO "sample_book_styles" VALUES('sample-018','#0369a1','#38bdf8');
INSERT INTO "sample_book_styles" VALUES('sample-019','#ca8a04','#f59e0b');
INSERT INTO "sample_book_styles" VALUES('sample-020','#db2777','#fb7185');
INSERT INTO "sample_book_styles" VALUES('sample-021','#4f46e5','#06b6d4');
INSERT INTO "sample_book_styles" VALUES('sample-022','#475569','#64748b');
INSERT INTO "sample_book_styles" VALUES('sample-023','#ea580c','#facc15');
INSERT INTO "sample_book_styles" VALUES('sample-024','#16a34a','#84cc16');
INSERT INTO "sample_book_styles" VALUES('sample-025','#2563eb','#7c3aed');
INSERT INTO "sample_book_styles" VALUES('sample-026','#059669','#14b8a6');
INSERT INTO "sample_book_styles" VALUES('sample-027','#dc2626','#f97316');
INSERT INTO "sample_book_styles" VALUES('sample-028','#9333ea','#ec4899');
INSERT INTO "sample_book_styles" VALUES('sample-029','#0f766e','#65a30d');
INSERT INTO "sample_book_styles" VALUES('sample-030','#0369a1','#38bdf8');
INSERT INTO "sample_book_styles" VALUES('sample-031','#ca8a04','#f59e0b');
INSERT INTO "sample_book_styles" VALUES('sample-032','#db2777','#fb7185');
INSERT INTO "sample_book_styles" VALUES('sample-033','#4f46e5','#06b6d4');
INSERT INTO "sample_book_styles" VALUES('sample-034','#475569','#64748b');
INSERT INTO "sample_book_styles" VALUES('sample-035','#ea580c','#facc15');
INSERT INTO "sample_book_styles" VALUES('sample-036','#16a34a','#84cc16');
INSERT INTO "sample_book_styles" VALUES('sample-037','#2563eb','#7c3aed');
INSERT INTO "sample_book_styles" VALUES('sample-038','#059669','#14b8a6');
INSERT INTO "sample_book_styles" VALUES('sample-039','#dc2626','#f97316');
INSERT INTO "sample_book_styles" VALUES('sample-040','#9333ea','#ec4899');
INSERT INTO "sample_book_styles" VALUES('sample-041','#0f766e','#65a30d');
INSERT INTO "sample_book_styles" VALUES('sample-042','#0369a1','#38bdf8');
INSERT INTO "sample_book_styles" VALUES('sample-043','#ca8a04','#f59e0b');
INSERT INTO "sample_book_styles" VALUES('sample-044','#db2777','#fb7185');
INSERT INTO "sample_book_styles" VALUES('sample-045','#4f46e5','#06b6d4');
INSERT INTO "sample_book_styles" VALUES('sample-046','#475569','#64748b');
INSERT INTO "sample_book_styles" VALUES('sample-047','#ea580c','#facc15');
INSERT INTO "sample_book_styles" VALUES('sample-048','#16a34a','#84cc16');
INSERT INTO "sample_book_styles" VALUES('sample-049','#2563eb','#7c3aed');
INSERT INTO "sample_book_styles" VALUES('sample-050','#059669','#14b8a6');
INSERT INTO "sample_book_styles" VALUES('sample-051','#dc2626','#f97316');
INSERT INTO "sample_book_styles" VALUES('sample-052','#9333ea','#ec4899');
INSERT INTO "sample_book_styles" VALUES('sample-053','#0f766e','#65a30d');
INSERT INTO "sample_book_styles" VALUES('sample-054','#0369a1','#38bdf8');
INSERT INTO "sample_book_styles" VALUES('sample-055','#ca8a04','#f59e0b');
INSERT INTO "sample_book_styles" VALUES('sample-056','#db2777','#fb7185');
INSERT INTO "sample_book_styles" VALUES('sample-057','#4f46e5','#06b6d4');
INSERT INTO "sample_book_styles" VALUES('sample-058','#475569','#64748b');
INSERT INTO "sample_book_styles" VALUES('sample-059','#ea580c','#facc15');
INSERT INTO "sample_book_styles" VALUES('sample-060','#16a34a','#84cc16');
INSERT INTO "sample_book_styles" VALUES('sample-061','#2563eb','#7c3aed');
INSERT INTO "sample_book_styles" VALUES('sample-062','#059669','#14b8a6');
INSERT INTO "sample_book_styles" VALUES('sample-063','#dc2626','#f97316');
INSERT INTO "sample_book_styles" VALUES('sample-064','#9333ea','#ec4899');
INSERT INTO "sample_book_styles" VALUES('sample-065','#0f766e','#65a30d');
INSERT INTO "sample_book_styles" VALUES('sample-066','#0369a1','#38bdf8');
INSERT INTO "sample_book_styles" VALUES('sample-067','#ca8a04','#f59e0b');
INSERT INTO "sample_book_styles" VALUES('sample-068','#db2777','#fb7185');
INSERT INTO "sample_book_styles" VALUES('sample-069','#4f46e5','#06b6d4');
INSERT INTO "sample_book_styles" VALUES('sample-070','#475569','#64748b');
INSERT INTO "sample_book_styles" VALUES('sample-071','#ea580c','#facc15');
INSERT INTO "sample_book_styles" VALUES('sample-072','#16a34a','#84cc16');
INSERT INTO "sample_book_styles" VALUES('sample-073','#2563eb','#7c3aed');
INSERT INTO "sample_book_styles" VALUES('sample-074','#059669','#14b8a6');
INSERT INTO "sample_book_styles" VALUES('sample-075','#dc2626','#f97316');
INSERT INTO "sample_book_styles" VALUES('sample-076','#9333ea','#ec4899');
INSERT INTO "sample_book_styles" VALUES('sample-077','#0f766e','#65a30d');
INSERT INTO "sample_book_styles" VALUES('sample-078','#0369a1','#38bdf8');
INSERT INTO "sample_book_styles" VALUES('sample-079','#ca8a04','#f59e0b');
INSERT INTO "sample_book_styles" VALUES('sample-080','#db2777','#fb7185');
INSERT INTO "sample_book_styles" VALUES('sample-081','#4f46e5','#06b6d4');
INSERT INTO "sample_book_styles" VALUES('sample-082','#475569','#64748b');
INSERT INTO "sample_book_styles" VALUES('sample-083','#ea580c','#facc15');
INSERT INTO "sample_book_styles" VALUES('sample-084','#16a34a','#84cc16');
INSERT INTO "sample_book_styles" VALUES('sample-085','#2563eb','#7c3aed');
INSERT INTO "sample_book_styles" VALUES('sample-086','#059669','#14b8a6');
INSERT INTO "sample_book_styles" VALUES('sample-087','#dc2626','#f97316');
INSERT INTO "sample_book_styles" VALUES('sample-088','#9333ea','#ec4899');
INSERT INTO "sample_book_styles" VALUES('sample-089','#0f766e','#65a30d');
INSERT INTO "sample_book_styles" VALUES('sample-090','#0369a1','#38bdf8');
INSERT INTO "sample_book_styles" VALUES('sample-091','#ca8a04','#f59e0b');
INSERT INTO "sample_book_styles" VALUES('sample-092','#db2777','#fb7185');
INSERT INTO "sample_book_styles" VALUES('sample-093','#4f46e5','#06b6d4');
INSERT INTO "sample_book_styles" VALUES('sample-094','#475569','#64748b');
INSERT INTO "sample_book_styles" VALUES('sample-095','#ea580c','#facc15');
INSERT INTO "sample_book_styles" VALUES('sample-096','#16a34a','#84cc16');
INSERT INTO "sample_book_styles" VALUES('sample-097','#2563eb','#7c3aed');
INSERT INTO "sample_book_styles" VALUES('sample-098','#059669','#14b8a6');
INSERT INTO "sample_book_styles" VALUES('sample-099','#dc2626','#f97316');
INSERT INTO "sample_book_styles" VALUES('sample-100','#9333ea','#ec4899');
CREATE TABLE sample_public_reviews (
              book_id TEXT NOT NULL,
              author TEXT NOT NULL,
              content TEXT NOT NULL,
              stars INTEGER NOT NULL,
              likes INTEGER NOT NULL
            );
INSERT INTO "sample_public_reviews" VALUES('sample-001','演示用户 A','这本示例书把“本地优先”和“长期归档”讲得很清楚，适合给工具型产品做说明。',5,42);
INSERT INTO "sample_public_reviews" VALUES('sample-001','演示用户 B','章节短，观点密度高，读完很容易整理成自己的工作流。',4,18);
INSERT INTO "sample_public_reviews" VALUES('sample-001','演示用户 C','最有启发的是把笔记当作可查询数据库，而不是静态文本。',5,31);
CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at INTEGER NOT NULL
);
INSERT INTO "schema_migrations" VALUES(3,1782456038);
CREATE TABLE sync_runs (
  id INTEGER PRIMARY KEY,
  started_at INTEGER NOT NULL,
  completed_at INTEGER,
  status TEXT NOT NULL,
  scope TEXT NOT NULL,
  detail TEXT
);
INSERT INTO "sync_runs" VALUES(1,1782403180,1782403200,'success','sample','generated fake sample data');
CREATE TABLE sync_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE TABLE thoughts (
  review_id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
  chapter_uid INTEGER,
  chapter_name TEXT,
  content TEXT,
  star INTEGER,
  text_range TEXT,
  is_book_review INTEGER NOT NULL DEFAULT 0,
  create_time INTEGER,
  updated_at INTEGER NOT NULL
);
INSERT INTO "thoughts" VALUES('sample-thought-1','sample-001',4,'第三章 与 AI 协作','结构化笔记适合交给 agent 做检索和复盘，但原始数据仍应留在本机。',5,'420-450',0,1780588800,1782403200);
CREATE INDEX idx_pop_book ON popular_highlights(book_id);
CREATE INDEX idx_books_sort ON books(sort DESC);
CREATE INDEX idx_highlights_book ON highlights(book_id);
CREATE INDEX idx_thoughts_book ON thoughts(book_id);
CREATE INDEX idx_stats_mode_time ON reading_stats(mode, fetched_at DESC);
COMMIT;
