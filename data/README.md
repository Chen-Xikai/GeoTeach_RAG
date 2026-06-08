# 数据目录说明

此目录用于存储 GeoTeach RAG 的所有数据文件。

## 目录结构

```
data/
├── docs/                    # 通用文档目录
├── textbook/                # 课本资料
├── curriculum/              # 课程标准
├── lesson_plan/             # 教案库
├── study_plan/              # 学案库
├── excellent_lesson/        # 优秀教案
├── excellent_study/         # 优秀学案
├── speech_draft/            # 说课稿
├── lecture_draft/           # 讲课稿
├── generated/               # AI生成的内容
├── images/                  # 提取的图片
├── cache/                   # Embedding缓存
└── milvus.db                # Milvus Lite 向量数据库
```

## 使用说明

### 上传资料
将教学资料放入对应的目录：
- **课本资料** → `textbook/`
- **课程标准** → `curriculum/`
- **教案** → `lesson_plan/`
- **学案** → `study_plan/`
- **优秀教案** → `excellent_lesson/`
- **优秀学案** → `excellent_study/`
- **说课稿** → `speech_draft/`
- **讲课稿** → `lecture_draft/`

### 支持的文件格式
- PDF (.pdf)
- Word (.docx)
- PowerPoint (.pptx)
- 文本文件 (.txt)
- Markdown (.md)

### 注意事项
- `milvus.db` 由系统自动管理，请勿手动修改
- `generated/` 目录存储AI生成的内容
- `cache/` 目录存储Embedding缓存，可安全删除重建
- 建议按教材章节组织文件命名
