#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 ASE 批量将 .xsd 文件转换为 .cif 文件，
强制原子坐标保留5位小数，晶胞参数保留4位小数。
方法：定位 _atom_site_occupancy 之后的数据块，直接修改坐标列。
"""

import os
import io
from ase.io import read
from ase.io.cif import write_cif

# ==================== 用户配置区域 ====================
input_dir = r"D:\Users\logic\Documents\Materials Studio Projects\Cu_Files\Documents\NEB"
output_dir = r"D:\lyf\calculation\Cu\NEB\IS-POSCAR"
coord_decimals = 5
cell_decimals = 4
skip_existing = True
# =====================================================

def fix_cif_simple(cif_content, cell_decimals, coord_decimals):
    """简单修复：晶胞参数按关键词替换，原子坐标定位 _atom_site_occupancy 之后的数据块修改"""
    lines = cif_content.splitlines()
    new_lines = []
    in_data_block = False  # 是否在原子数据块内

    cell_keys = ['_cell_length_a', '_cell_length_b', '_cell_length_c',
                 '_cell_angle_alpha', '_cell_angle_beta', '_cell_angle_gamma']

    for line in lines:
        stripped = line.strip()
        # 处理晶胞参数行
        if any(stripped.startswith(key) for key in cell_keys):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    value = float(parts[-1])
                    parts[-1] = f"{value:.{cell_decimals}f}"
                    new_lines.append(' '.join(parts))
                except:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            continue

        # 检测数据块开始：包含 _atom_site_occupancy 的行，下一行开始是数据
        if '_atom_site_occupancy' in stripped:
            in_data_block = True
            new_lines.append(line)
            continue

        # 如果在数据块内，处理原子数据行
        if in_data_block:
            # 数据行通常以空格分隔，且至少6列（元素 标签 占据数 x y z ...）
            parts = line.split()
            if len(parts) >= 6:
                try:
                    # 假设 x,y,z 在第4,5,6列（索引3,4,5）
                    x = float(parts[3])
                    y = float(parts[4])
                    z = float(parts[5])
                    parts[3] = f"{x:.{coord_decimals}f}"
                    parts[4] = f"{y:.{coord_decimals}f}"
                    parts[5] = f"{z:.{coord_decimals}f}"
                    new_lines.append(' '.join(parts))
                except (ValueError, IndexError):
                    # 如果不是数字或列数不够，退出数据块（比如遇到空行）
                    in_data_block = False
                    new_lines.append(line)
            else:
                # 如果行字段数不足6，可能数据块结束（如空行或新loop）
                in_data_block = False
                new_lines.append(line)
        else:
            new_lines.append(line)

    return '\n'.join(new_lines)

def main():
    print("=== 批量转换 .xsd -> .cif (晶胞4位，坐标5位) 简化版 ===")
    if not os.path.isdir(input_dir):
        print(f"错误：输入文件夹不存在 -> {input_dir}")
        return
    print(f"输入文件夹: {input_dir}")
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出文件夹: {output_dir}")

    total = converted = skipped = failed = 0

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith('.xsd'):
            continue
        total += 1
        xsd_path = os.path.join(input_dir, filename)
        base_name = filename[:-4]
        cif_name = base_name + '.cif'
        cif_path = os.path.join(output_dir, cif_name)

        print(f"\n处理文件: {filename}")

        if skip_existing and os.path.exists(cif_path):
            print(f"  跳过：{cif_name} 已存在")
            skipped += 1
            continue

        try:
            # 读取 .xsd
            atoms = read(xsd_path)
            if len(atoms) == 0:
                print(f"  错误：原子数为0，可能读取失败")
                failed += 1
                continue

            # 写入CIF到内存字节流
            with io.BytesIO() as buf:
                write_cif(buf, atoms)
                raw_cif_bytes = buf.getvalue()
            raw_cif = raw_cif_bytes.decode('utf-8')

            # 简化修复
            fixed_cif = fix_cif_simple(raw_cif, cell_decimals, coord_decimals)

            # 写入文件
            with open(cif_path, 'w', encoding='utf-8') as f:
                f.write(fixed_cif)

            file_size = os.path.getsize(cif_path)
            print(f"  成功，文件大小: {file_size} 字节")
            # 预览前5行
            with open(cif_path, 'r') as f:
                preview_lines = f.readlines()[:5]
            print("  预览前5行:")
            for line in preview_lines:
                print(f"    {line.rstrip()}")
            converted += 1

        except Exception as e:
            print(f"  错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n========== 完成 ==========")
    print(f"总文件数: {total}")
    print(f"成功转换: {converted}")
    print(f"跳过（已存在）: {skipped}")
    print(f"失败: {failed}")
    print(f"输出文件夹: {output_dir}")

if __name__ == "__main__":
    main()