#### Develop

1. Cài đặt môi trường dành cho nhà phát triển:

```bash
# Local
pip install -r requirements.txt

```

2. Format code stype

```bash
# Cài đặt pre-commit
pip install pre-commit

# Kích hoạt pre-commit
pre-commit install

# Test hooks
pre-commit run --all-files
```

3. Chạy môi trường phát triển với k8s

```bash
# Cài đặt công cụ Tilt cho việc triển khai k8s local
https://docs.tilt.dev/install.html

# Đi đến thư mục source code
cd <directory-path>

# Kích hoạt Tiltfile
sudo tilt up
```
