import time
import boto3
import os
import re
import subprocess
import json

# S3 bucket 名称
s3_bucket = "mua-nft-models"
account_id = "891377104861"


def convert_s3(gltf_model):
    # 检查文件名是否包含非法字符
    if re.search(r'[\\/*?:"<>|]', gltf_model):
        return {"status": "failure", "message": "Invalid characters in file name"}

    # 检查文件后缀
    if not (gltf_model.endswith('.glb') or gltf_model.endswith('.gltf')):
        return {"status": "failure", "message": "Invalid file extension"}

    # 创建S3客户端
    s3 = boto3.client('s3')

    # 下载glb文件到本地
    glb_file = '/tmp/' + os.path.basename(gltf_model)
    # print current working path
    print(os.getcwd())
    s3.download_file(s3_bucket, gltf_model, glb_file)

    # 转换glb文件为usdz文件

    # usdz_key 由glb_key替换后缀名得到 后缀名可能是GLB也可能是gltf
    usdz_key = gltf_model.replace('.glb', '.usdz').replace('.gltf', '.usdz')
    usdz_file = '/tmp/' + os.path.basename(usdz_key)

    try:
        # 从命令行调用usdzconvert
        print("start convert ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        subprocess.run(['./usdzconvert', glb_file, usdz_file], check=True)
        print("finish convert ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    except subprocess.CalledProcessError as e:
        # 转换失败
        print("convert error ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        return {"status": "failure", "message": str(e)}

    # 上传usdz文件到S3
    s3.upload_file(usdz_file, s3_bucket, usdz_key)

    # 删除本地的临时文件
    os.remove(glb_file)
    os.remove(usdz_file)

    # 转换成功
    usdz_url = f"https://{s3_bucket}.s3.amazonaws.com/{usdz_key}"
    return {"status": "success", "message": usdz_url}


def handler(event, context):
    model = event.get('model')
    result = convert_s3(model)
    # stringyfy the result
    return json.dumps(result)
