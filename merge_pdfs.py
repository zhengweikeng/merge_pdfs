from pypdf import PdfWriter, PdfReader
import os
import re
from PIL import Image
import io
import argparse

def natural_sort_key(s):
    """自然排序的键函数，正确处理数字序号"""
    # 将字符串分割成数字和非数字部分
    def convert(text):
        # 如果文本可以转换为整数，则转换
        return int(text) if text.isdigit() else text.lower()
    
    # 使用正则表达式分割字符串，保留数字和非数字部分
    return [convert(c) for c in re.split('([0-9]+)', s)]

def get_all_pdfs(input_dir, parent_bookmark=None, include_files=None, exclude_files=None):
    """递归获取所有PDF文件的路径和对应的书签结构"""
    pdf_structure = []
    
    # 获取目录下所有文件和文件夹
    items = os.listdir(input_dir)
    # 创建包含类型和路径的项目列表，便于统一排序
    all_items = []
    
    for item in items:
        full_path = os.path.join(input_dir, item)
        if os.path.isdir(full_path):
            all_items.append(('folder', item, full_path, False))
        elif item.endswith('.pdf'):
            # 检查是否应该包含此文件
            if include_files and item not in include_files:
                continue
            # 检查是否应该排除此文件
            if exclude_files and item in exclude_files:
                continue

            hasToC = isPdfHasTableOfContents(full_path)
            all_items.append(('pdf', item, full_path, hasToC))
    
    # 使用自然排序对所有项目进行排序
    all_items.sort(key=lambda x: natural_sort_key(x[1]))

    # 统一处理文件和文件夹
    for item_type, item_name, item_path, hasToC in all_items:
        if item_type == 'pdf':
            # 处理PDF文件
            bookmark_name = os.path.splitext(item_name)[0]
            pdf_structure.append({
                'path': item_path,
                'bookmark': bookmark_name,
                'parent': parent_bookmark,
                'hasToC': hasToC
            })
        else:
            # 处理文件夹，将文件夹名作为父书签
            folder_bookmark = item_name
            if parent_bookmark:
                folder_bookmark = f"{parent_bookmark}/{folder_bookmark}"
            
            # 递归处理子文件夹，传入当前文件夹名作为父书签
            sub_pdfs = get_all_pdfs(item_path, folder_bookmark, include_files, exclude_files)
            if sub_pdfs:  # 只有当子文件夹中有PDF文件时才添加
                # 添加文件夹作为父书签
                pdf_structure.append({
                    'path': None,  # 文件夹没有对应的PDF文件
                    'bookmark': item_name,
                    'parent': parent_bookmark,
                    'is_folder': True,
                    'hasToC': hasToC
                })
                pdf_structure.extend(sub_pdfs)
    
    return pdf_structure

def find_cover_image(input_dir):
    """查找封面图片文件"""
    supported_formats = ('.jpg', '.jpeg', '.png')
    for ext in supported_formats:
        cover_path = os.path.join(input_dir, f"cover{ext}")
        if os.path.exists(cover_path):
            return cover_path
    return None

def add_cover_page(merger, cover_path):
    """将封面图片添加为PDF的第一页"""
    # 打开图片
    cover_image = Image.open(cover_path)
    # 转换为RGB模式（如果是RGBA，去除alpha通道）
    if cover_image.mode == 'RGBA':
        cover_image = cover_image.convert('RGB')
    
    # 创建一个字节流来保存PDF格式的图片
    img_byte_arr = io.BytesIO()
    cover_image.save(img_byte_arr, format='PDF')
    img_byte_arr.seek(0)
    
    # 将封面添加到PDF
    merger.append(fileobj=img_byte_arr)
    return True

def isPdfHasTableOfContents(pdf_path):
    """检查PDF文件是否包含目录"""
    with open(pdf_path, 'rb') as pdf_file:
        reader = PdfReader(pdf_file)
        return reader.outline

def merge_pdfs(input_dir, output_file, include_files=None, exclude_files=None):
    # 检查输出文件是否已存在
    if os.path.exists(output_file):
        print(f"错误：输出文件 '{output_file}' 已存在。")
        print("请指定一个新的输出文件名，或删除现有文件后重试。")
        return False
    
    # 创建一个PdfWriter对象
    merger = PdfWriter()

    # 处理封面
    cover_path = find_cover_image(input_dir)
    has_cover = False
    if cover_path:
        has_cover = add_cover_page(merger, cover_path)
        print(f"已添加封面图片：{cover_path}")
    
    # 获取所有PDF文件及其书签结构，传入include和exclude参数
    pdf_files = get_all_pdfs(input_dir, include_files=include_files, exclude_files=exclude_files)
    
    # 用于跟踪页面编号
    current_page = 1 if has_cover else 0  # 如果有封面，从第2页开始计数
    bookmarks = {}  # 用于存储书签对象
    
    # 首先添加所有PDF文件
    for pdf_info in pdf_files:
        if not pdf_info.get('is_folder', False):
            file_path = pdf_info['path']
            merger.append(fileobj=file_path)
            
            # 记录当前PDF文件的页数，用于设置书签
            page_count = len(merger.pages)
            pdf_info['page_number'] = current_page
            current_page = page_count
    
    # 创建书签结构
    for pdf_info in pdf_files:
        bookmark_name = pdf_info['bookmark']
        parent_name = pdf_info['parent']
        hasToC = pdf_info['hasToC']
        
        # 获取父书签对象
        parent_bookmark = bookmarks.get(parent_name) if parent_name else None
        
        if pdf_info.get('is_folder', False):
            # 为文件夹创建书签（父节点）
            bookmark = merger.add_outline_item(
                bookmark_name,
                None,  # 文件夹不链接到具体页面
                parent=parent_bookmark
            )
            bookmarks[pdf_info['parent'] + '/' + bookmark_name if parent_name else bookmark_name] = bookmark
        else:
            # 为PDF文件创建书签（叶子节点）
            print(f"正在处理pdf: {bookmark_name}, {parent_bookmark}")
            if not hasToC:
                merger.add_outline_item(
                    bookmark_name,
                    pdf_info['page_number'],
                    parent=parent_bookmark
                )
    
    # 将合并后的文件保存到输出路径
    with open(output_file, 'wb') as output:
        merger.write(output)
    
    print(f"PDF文件已合并完成，输出文件：{output_file}")
    print(f"共合并了 {sum(1 for pdf in pdf_files if not pdf.get('is_folder', False))} 个PDF文件")
    return True

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='合并PDF文件并支持添加封面')
    parser.add_argument('-i', '--input', 
                        default='./pdfs',
                        help='输入目录路径，默认为 ./pdfs')
    parser.add_argument('-o', '--output',
                        default='merged_output.pdf',
                        help='输出文件名，默认为 merged_output.pdf')
    parser.add_argument('--include',
                        nargs='+',
                        help='指定要包含的PDF文件名列表（需要包含.pdf后缀）')
    parser.add_argument('--exclude',
                        nargs='+',
                        help='指定要排除的PDF文件名列表（需要包含.pdf后缀）')
    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置输入文件夹路径
    input_directory = args.input
    # 设置输出文件路径
    output_pdf = args.output
    
    # 如果输出路径不是绝对路径，则将其转换为相对于当前目录的路径
    if not os.path.isabs(output_pdf):
        output_pdf = os.path.join(os.getcwd(), output_pdf)
    
    # 确保输入目录存在
    if not os.path.exists(input_directory):
        os.makedirs(input_directory)
        print(f"已创建输入目录：{input_directory}")
    
    # 执行合并操作，传入include和exclude参数
    merge_pdfs(input_directory, output_pdf, args.include, args.exclude) 