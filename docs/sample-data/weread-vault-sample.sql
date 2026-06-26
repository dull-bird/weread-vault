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
INSERT INTO "books" VALUES('sample-001','星河笔记：在夜航中思考','林小满','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','工具与效率',NULL,0,0,0,12,87,NULL,1,10000,NULL,92.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-002','慢读花园','周青禾','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学随笔',NULL,0,0,0,8,64,NULL,0,9999,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-003','纸上城市漫游','陈亦舟','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学随笔',NULL,0,0,0,5,42,NULL,0,9998,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-004','把时间折成书签','顾南风','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','工具与效率',NULL,0,0,0,18,95,NULL,1,9997,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-005','一杯茶里的宇宙','宋知夏','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','科学通识',NULL,0,0,0,3,31,NULL,0,9996,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-006','清晨算法课','许明远','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','科学通识',NULL,0,0,0,15,76,NULL,0,9995,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-007','灯下的长期主义','叶澜','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','心理成长',NULL,0,0,0,6,54,NULL,0,9994,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-008','海边书店来信','白鹿','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学随笔',NULL,0,0,0,2,22,NULL,0,9993,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-009','示例小说：风从第七页来','赵栖迟','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','文学随笔',NULL,0,0,0,9,68,NULL,0,9992,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-010','索引与星图','孟遥','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','工具与效率',NULL,0,0,0,7,48,NULL,0,9991,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-011','假日观察手册','何西','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','心理成长',NULL,0,0,0,11,83,NULL,1,9990,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-012','给未来的阅读报告','沈安','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','工具与效率',NULL,0,0,0,4,39,NULL,0,9989,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-101','私人知识库小史','林小满','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','工具与效率',NULL,0,0,0,0,0,NULL,0,9988,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-102','离线工具的温度','林小满','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','工具与效率',NULL,0,0,0,0,0,NULL,0,9987,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-103','给 Agent 的索引课','林小满','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','工具与效率',NULL,0,0,0,0,0,NULL,0,9986,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-104','慢慢同步','林小满','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','工具与效率',NULL,0,0,0,0,0,NULL,0,9985,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-105','笔记与边界','林小满','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','工具与效率',NULL,0,0,0,0,0,NULL,0,9984,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
INSERT INTO "books" VALUES('sample-106','每周读书实验','林小满','','这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。','工具与效率',NULL,0,0,0,0,0,NULL,0,9983,NULL,80.0,NULL,128000,'示例出版社',NULL,NULL,1782403200);
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
INSERT INTO "reading_stats" VALUES(1,'overall',0,'{"totalReadTime": 153000, "readDays": 36, "readTimes": {"1735660800": 64800, "1767196800": 88200}, "readLongest": [{"book": {"title": "星河笔记：在夜航中思考", "author": "林小满"}, "readTime": 7400}, {"book": {"title": "慢读花园", "author": "周青禾"}, "readTime": 5200}, {"book": {"title": "清晨算法课", "author": "许明远"}, "readTime": 3900}, {"book": {"title": "灯下的长期主义", "author": "叶澜"}, "readTime": 2600}], "preferCategory": [{"categoryTitle": "工具与效率", "readingTime": 15000, "readingCount": 8}, {"categoryTitle": "文学随笔", "readingTime": 9100, "readingCount": 7}, {"categoryTitle": "科学通识", "readingTime": 6300, "readingCount": 5}, {"categoryTitle": "心理成长", "readingTime": 4200, "readingCount": 4}], "preferAuthor": [{"name": "林小满", "count": 9, "readTime": "9 次"}, {"name": "周青禾", "count": 6, "readTime": "6 次"}, {"name": "陈亦舟", "count": 4, "readTime": "4 次"}, {"name": "顾南风", "count": 3, "readTime": "3 次"}], "preferTime": [0, 0, 0, 0, 0, 0, 1, 3, 5, 4, 3, 2, 2, 4, 6, 8, 7, 5, 4, 3, 2, 1, 0, 0], "readStat": [{"stat": "读过", "counts": "24本"}], "preferCategoryWord": "工具与效率", "preferTimeWord": "傍晚阅读较多"}',1782403200);
INSERT INTO "reading_stats" VALUES(2,'annually',0,'{"totalReadTime": 153000, "readDays": 36, "readTimes": {"1735660800": 64800, "1767196800": 88200}, "readLongest": [{"book": {"title": "星河笔记：在夜航中思考", "author": "林小满"}, "readTime": 7400}, {"book": {"title": "慢读花园", "author": "周青禾"}, "readTime": 5200}, {"book": {"title": "清晨算法课", "author": "许明远"}, "readTime": 3900}, {"book": {"title": "灯下的长期主义", "author": "叶澜"}, "readTime": 2600}], "preferCategory": [{"categoryTitle": "工具与效率", "readingTime": 15000, "readingCount": 8}, {"categoryTitle": "文学随笔", "readingTime": 9100, "readingCount": 7}, {"categoryTitle": "科学通识", "readingTime": 6300, "readingCount": 5}, {"categoryTitle": "心理成长", "readingTime": 4200, "readingCount": 4}], "preferAuthor": [{"name": "林小满", "count": 9, "readTime": "9 次"}, {"name": "周青禾", "count": 6, "readTime": "6 次"}, {"name": "陈亦舟", "count": 4, "readTime": "4 次"}, {"name": "顾南风", "count": 3, "readTime": "3 次"}], "preferTime": [0, 0, 0, 0, 0, 0, 1, 3, 5, 4, 3, 2, 2, 4, 6, 8, 7, 5, 4, 3, 2, 1, 0, 0], "readStat": [{"stat": "读过", "counts": "24本"}], "preferCategoryWord": "工具与效率", "preferTimeWord": "傍晚阅读较多"}',1782403200);
INSERT INTO "reading_stats" VALUES(3,'monthly',0,'{"totalReadTime": 153000, "readDays": 36, "readTimes": {"1735660800": 64800, "1767196800": 88200}, "readLongest": [{"book": {"title": "星河笔记：在夜航中思考", "author": "林小满"}, "readTime": 7400}, {"book": {"title": "慢读花园", "author": "周青禾"}, "readTime": 5200}, {"book": {"title": "清晨算法课", "author": "许明远"}, "readTime": 3900}, {"book": {"title": "灯下的长期主义", "author": "叶澜"}, "readTime": 2600}], "preferCategory": [{"categoryTitle": "工具与效率", "readingTime": 15000, "readingCount": 8}, {"categoryTitle": "文学随笔", "readingTime": 9100, "readingCount": 7}, {"categoryTitle": "科学通识", "readingTime": 6300, "readingCount": 5}, {"categoryTitle": "心理成长", "readingTime": 4200, "readingCount": 4}], "preferAuthor": [{"name": "林小满", "count": 9, "readTime": "9 次"}, {"name": "周青禾", "count": 6, "readTime": "6 次"}, {"name": "陈亦舟", "count": 4, "readTime": "4 次"}, {"name": "顾南风", "count": 3, "readTime": "3 次"}], "preferTime": [0, 0, 0, 0, 0, 0, 1, 3, 5, 4, 3, 2, 2, 4, 6, 8, 7, 5, 4, 3, 2, 1, 0, 0], "readStat": [{"stat": "读过", "counts": "24本"}], "preferCategoryWord": "工具与效率", "preferTimeWord": "傍晚阅读较多"}',1782403200);
INSERT INTO "reading_stats" VALUES(4,'weekly',0,'{"totalReadTime": 153000, "readDays": 36, "readTimes": {"1735660800": 64800, "1767196800": 88200}, "readLongest": [{"book": {"title": "星河笔记：在夜航中思考", "author": "林小满"}, "readTime": 7400}, {"book": {"title": "慢读花园", "author": "周青禾"}, "readTime": 5200}, {"book": {"title": "清晨算法课", "author": "许明远"}, "readTime": 3900}, {"book": {"title": "灯下的长期主义", "author": "叶澜"}, "readTime": 2600}], "preferCategory": [{"categoryTitle": "工具与效率", "readingTime": 15000, "readingCount": 8}, {"categoryTitle": "文学随笔", "readingTime": 9100, "readingCount": 7}, {"categoryTitle": "科学通识", "readingTime": 6300, "readingCount": 5}, {"categoryTitle": "心理成长", "readingTime": 4200, "readingCount": 4}], "preferAuthor": [{"name": "林小满", "count": 9, "readTime": "9 次"}, {"name": "周青禾", "count": 6, "readTime": "6 次"}, {"name": "陈亦舟", "count": 4, "readTime": "4 次"}, {"name": "顾南风", "count": 3, "readTime": "3 次"}], "preferTime": [0, 0, 0, 0, 0, 0, 1, 3, 5, 4, 3, 2, 2, 4, 6, 8, 7, 5, 4, 3, 2, 1, 0, 0], "readStat": [{"stat": "读过", "counts": "24本"}], "preferCategoryWord": "工具与效率", "preferTimeWord": "傍晚阅读较多"}',1782403200);
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
INSERT INTO "sample_book_styles" VALUES('sample-101','#1d4ed8','#22c55e');
INSERT INTO "sample_book_styles" VALUES('sample-102','#7c2d12','#f97316');
INSERT INTO "sample_book_styles" VALUES('sample-103','#581c87','#a855f7');
INSERT INTO "sample_book_styles" VALUES('sample-104','#0f766e','#14b8a6');
INSERT INTO "sample_book_styles" VALUES('sample-105','#be123c','#fb7185');
INSERT INTO "sample_book_styles" VALUES('sample-106','#334155','#94a3b8');
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
INSERT INTO "schema_migrations" VALUES(3,1782444947);
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
