StructurePPTGenerator 使用文档
=====================================

概述

StructurePPTGenerator 是一个 Python 类，用于从指定目录读取晶体结构的投影图像（俯视图、主视图、侧视图），并自动生成 PowerPoint 演示文稿。每个结构的图像按命名规则组织，生成 PPT 时每页可放置 1 至 3 个结构，结构在页面上水平排列，每个结构内部包含结构名称（可选）、上方的俯视图、下方的主视图和/或侧视图。图像尺寸根据分配的区域高度和原始宽高比智能计算，并在区域内居中显示。

适用场景：批量展示多个晶体结构的三个视图（俯视、主视、侧视），自动生成排版美观的 PPT，支持缺少其中一个侧向视图的情况。

依赖环境

Python >= 3.7
必需库：
python-pptx 用于生成 PPT 文件
Pillow (PIL) 用于读取图像尺寸（获取宽高比）
安装命令（在命令行中执行）：
pip install python-pptx Pillow

文件结构要求

您需要先将所有结构的图像保存在同一个目录下（例如 D:\cif_images）。图像命名必须遵循以下规则：
每个结构有一个唯一的前缀（prefix），例如 sample1、sample2。
每个结构必须包含一张俯视图，文件名为 prefix_top.png
每个结构应至少包含一张侧向视图，可以是主视图（front）或侧视图（side），或两者都有：
prefix_front.png (主视图)
prefix_side.png (侧视图)

示例目录内容：
D:\cif_images
sample1_top.png
sample1_front.png
sample1_side.png
sample2_top.png
sample2_front.png (缺少 side.png 也可以)
sample3_top.png
sample3_side.png (缺少 front.png 也可以)

注意：所有图像格式必须为 PNG，文件名严格区分大小写不敏感（程序会自动识别大小写），但推荐统一使用小写。

类初始化

class StructurePPTGenerator(image_dir)

参数：
image_dir : str，必填。存放所有结构图像的目录路径（Windows 路径建议使用原始字符串，如 r"D:\cif_images"）。程序会递归扫描该目录下的 PNG 文件，根据文件名前缀自动分组。

初始化后会立即扫描目录，打印加载的结构数量及前缀列表。如果目录不存在或没有找到有效的结构（缺少 top 图或没有任何侧向视图），会抛出 ValueError。

主要方法

generate_ppt(output_path, structures_per_slide)

功能：根据已加载的结构生成 PPT 文件。

参数：
output_path : str，必填。输出 PPT 文件的完整路径（例如 r"D:\presentation.pptx"）。如果目录不存在会自动创建。
structures_per_slide : int，必填。每页放置的结构数量，只能为 1、2 或 3。程序会按结构扫描顺序依次填入页面。

返回值：无。生成的文件保存在指定路径，同时控制台打印成功信息。