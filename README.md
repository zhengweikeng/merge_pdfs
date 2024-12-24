# PDF合并工具 (PDF Merger)

一个简单的PDF文件合并工具，使用Python开发。

## 功能特点

- 支持多个PDF文件合并
- 保持原始PDF文件的格式和质量
- 支持根据PDF所在文件夹生成目录

## 安装要求

确保您的系统已安装以下依赖：

- Python 3.8+
- pip
- 安装依赖：`pip install -r requirements.txt`

## 使用方法

```
git clone git@github.com:zhengweikeng/merge_pdfs.git
cd pdf-merger
pip install -r requirements.txt
mkdir pdfs
mv some_pdf_files.pdf pdfs/
python merge_pdfs.py
```

## 参数

- `-i` 或 `--input`：输入目录路径，默认为 `./pdfs`
- `-o` 或 `--output`：输出文件名，默认为 `merged_output.pdf`
- `--include`：指定要包含的PDF文件名列表（需要包含.pdf后缀）
- `--exclude`：指定要排除的PDF文件名列表（需要包含.pdf后缀）

## 贡献指南

欢迎提交问题和改进建议，请提交到GitHub仓库。

## 许可证

本项目采用MIT许可证，详情请参阅LICENSE文件。
