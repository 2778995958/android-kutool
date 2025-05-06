以GPT4o-mini寫。


配合[UnpackKindleS](https://github.com/Aeroblast/UnpackKindleS)使用藍疊，而不必打開carlibre一鍵出epub

結合

日亚4月23日后新书提取[教程](https://books.fishhawk.top/forum/680f133909bd607077257da8)

日亚4月23日后新书提取改高清图[教程](https://books.fishhawk.top/forum/6810a15109bd6070772647fc)


### 事前是你已經成功過一次，本python用於第二次以後

1)自動找到端口

2)自動加書carlibre

3)自動拆成epub(res)

4)自動刪carlibre書庫


### 準備的東西

UnpackKindleS

python

carlibre(不要改安裝位置)，做AZW6 Image Merge和dedrm安裝，已加入backup.ab在裡面

藍疊

SDK Platform Tools放在UnpackKindleS資料夾

UnpackKindleS資料夾目錄下應該是有(全路徑不可以有中文)

UnpackKindleS/app

UnpackKindleS/platform-tools

UnpackKindleS/_Tool_adb_bs_carlibre_epub.py


### 做法
打開藍疊(不可以有多於一個案例開啟adb，否則找不到端口)
下載書
雙擊_Tool_adb_bs_carlibre_epub.py
輸出epub

注意：當你拆完一次後，如果你不刪android資料夾，第二次拆書會重複拆

如果你的UnpackKindleS放在別地方，可以改位置，但SDK Platform Tools請放在裡面

unpack_kindle_base_path = current_dir  # 預設為當前目錄

unpack_kindle_base_path = r'E:\UnpackKindleS'  # 可修改為實際路徑
