import os
import subprocess
import re
import shutil
import xml.etree.ElementTree as ET

# 獲取當前目錄
current_dir = os.path.dirname(os.path.abspath(__file__))
android_directory = os.path.join(current_dir, 'android')

# 預設 UnpackKindleS 路徑（可根據需要修改）
unpack_kindle_base_path = current_dir  # 預設為當前目錄
# unpack_kindle_base_path = r'E:\UnpackKindleS'  # 可修改為實際路徑
unpack_kindle_path = os.path.join(unpack_kindle_base_path, 'app', 'UnpackKindleS.exe')
platform_tools_dir = os.path.join(unpack_kindle_base_path, 'platform-tools')

# 查找 HD-Player.exe 的 PID
pid_cmd = 'tasklist | findstr HD-Player.exe'
try:
    pid_output = subprocess.check_output(pid_cmd, shell=True, text=True)

    # 提取 PID
    pid = None
    for line in pid_output.splitlines():
        match = re.search(r'HD-Player\.exe\s+(\d+)', line)
        if match:
            pid = match.group(1)
            break

    if pid is None:
        print("未找到 HD-Player.exe 的 PID，將跳過 ADB 操作。")
    else:
        # 查找對應的端口
        netstat_cmd = f'netstat -ano | findstr LISTENING | findstr {pid}'
        netstat_output = subprocess.check_output(netstat_cmd, shell=True, text=True)

        port = None
        for line in netstat_output.splitlines():
            match = re.search(r'TCP\s+127\.0\.0\.1:(\d+)', line)
            if match:
                port = match.group(1)
                break

        if port is None:
            print("未找到對應的端口，將跳過 ADB 操作。")
        else:
            # 使用 ADB 連接並拉取文件
            adb_connect_cmd = f'adb connect 127.0.0.1:{port}'
            adb_pull_cmd = f'adb -s 127.0.0.1:{port} pull /sdcard/Android/data/com.amazon.kindle/files/. {android_directory}'

            os.chdir(platform_tools_dir)

            # 執行 ADB 命令
            subprocess.run(adb_connect_cmd, shell=True)
            subprocess.run(adb_pull_cmd, shell=True)

            print("完成文件拉取。")

except subprocess.CalledProcessError:
    print("執行命令時出錯，將跳過 ADB 操作。")

# 檢查 android 資料夾是否存在
if not os.path.exists(android_directory):
    print("未找到 android 資料夾，程式將結束。")
    exit(1)

def clean_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def rename_ast_to_res(android_directory):
    for dirpath, dirnames, filenames in os.walk(android_directory):
        for filename in filenames:
            if filename.endswith('.ast'):
                ast_file_path = os.path.join(dirpath, filename)
                res_file_path = os.path.join(dirpath, filename.replace('.ast', '.res'))
                os.rename(ast_file_path, res_file_path)
                print(f"檔案 {ast_file_path} 已改名為: {res_file_path}")

def extract_book_id(output):
    match = re.search(r'id：(\d+)', output)
    if match:
        return match.group(1)
    return None

def add_books_to_calibre(android_directory):
    added_ids = []
    for entry in os.listdir(android_directory):
        entry_path = os.path.join(android_directory, entry)
        if os.path.isdir(entry_path):
            for filename in os.listdir(entry_path):
                if filename.endswith('.prc'):
                    file_path = os.path.join(entry_path, filename)
                    result = subprocess.run(
                        ['calibredb', 'add', file_path],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    if result.returncode == 0:
                        book_id = extract_book_id(result.stdout)
                        if book_id:
                            added_ids.append(book_id)
                            print(f"已添加書籍: {file_path}，ID: {book_id}")
                    else:
                        print(f"錯誤: {result.stderr.strip()}")
    return added_ids

def remove_books_from_calibre(added_ids):
    for book_id in added_ids:
        subprocess.run(['calibredb', 'remove', book_id])
        print(f"已刪除書籍 ID: {book_id}")
        caltrash_directory = os.path.join(os.path.expanduser('~'), 'calibre 書庫', '.caltrash', 'b', book_id)
        if os.path.exists(caltrash_directory):
            shutil.rmtree(caltrash_directory)
            print(f"已刪除 .caltrash 資料夾: {caltrash_directory}")

def azw3_to_asin():
    root_directory = os.path.join(os.path.expanduser('~'), 'calibre 書庫')
    added_ids = add_books_to_calibre(android_directory)

    for dirpath, dirnames, filenames in os.walk(root_directory):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]

        azw3_files = [f for f in filenames if f.endswith('.azw3')]

        for filename in filenames:
            if filename.endswith('.opf'):
                opf_path = os.path.join(dirpath, filename)
                print(f"處理 OPF 檔案: {opf_path}")

                tree = ET.parse(opf_path)
                root = tree.getroot()

                asin = None
                ns = {'dc': 'http://purl.org/dc/elements/1.1/', 'opf': 'http://www.idpf.org/2007/opf'}
                for identifier in root.findall('.//dc:identifier', ns):
                    if identifier.attrib.get('{http://www.idpf.org/2007/opf}scheme') == 'MOBI-ASIN':
                        asin = identifier.text
                        print(f"找到 ASIN: {asin}")
                        break

                if asin:
                    cleaned_asin = clean_filename(asin)
                    new_asin_folder_path = os.path.join(android_directory, f"{cleaned_asin}_EBOK")

                    # 檢查資料夾是否已存在
                    if os.path.exists(new_asin_folder_path):
                        print(f"資料夾 {new_asin_folder_path} 已存在，跳過添加書籍。")
                        continue  # 跳過到下一個檔案

                    asin_folder_path = os.path.join(android_directory, cleaned_asin)

                    if not os.path.exists(asin_folder_path):
                        os.makedirs(asin_folder_path)

                    for azw3_filename in azw3_files:
                        cleaned_filename = clean_filename(azw3_filename)
                        azw3_path = os.path.join(dirpath, azw3_filename)
                        print(f"對應的 AZW3 檔案: {azw3_path}")

                        new_file_path = os.path.join(asin_folder_path, f"{cleaned_asin}.azw3")
                        shutil.copy(azw3_path, new_file_path)
                        print(f"檔案 {cleaned_filename} 已複製到: {new_file_path}")

                    os.rename(asin_folder_path, new_asin_folder_path)
                    print(f"資料夾已改名為: {new_asin_folder_path}")

                    rename_ast_to_res(android_directory)

                    break
                else:
                    print(f"錯誤: {filename} 未找到 ASIN.")

    remove_books_from_calibre(added_ids)

def unpack_kindle(android_directory):
    # 確保在 UnpackKindleS 的 app 資料夾中執行
    app_directory = os.path.join(unpack_kindle_base_path, 'app')
    os.chdir(app_directory)

    command = [
        unpack_kindle_path,
        os.path.join(android_directory),
        os.path.dirname(android_directory),
        '-dedrm',
        '-batch',
        '--rename-xhtml-with-id',
        '--overwrite'
    ]
    
    # 執行命令並顯示輸出
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')

    # 逐行讀取輸出
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())  # 顯示輸出

    return_code = process.wait()
    if return_code == 0:
        print("UnpackKindleS 執行成功。")
    else:
        print(f"UnpackKindleS 執行失敗: {process.stderr.read().strip()}")

# 執行所有步驟
azw3_to_asin()
unpack_kindle(android_directory)

# 暫停
input("按 Enter 鍵以結束...")