import http.client, mimetypes, json, os, sys, time
file_path = r"C:\Users\hp\OneDrive\Desktop\Files\Medical Flutter App\backend\temp_test.pdf"
if not os.path.exists(file_path):
    print('missing file', file_path)
    sys.exit(1)
with open(file_path, 'rb') as f:
    data = f.read()
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
crlf = '\r\n'
mime_type = mimetypes.guess_type(file_path)[0] or 'application/pdf'
body = []
body.append(f'--{boundary}{crlf}')
body.append(f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file_path)}"{crlf}')
body.append(f'Content-Type: {mime_type}{crlf}{crlf}')
body_bytes = body[0].encode() + body[1].encode() + body[2].encode() + data + crlf.encode()
body_bytes += f'--{boundary}--{crlf}'.encode()
headers = {
    'Content-Type': f'multipart/form-data; boundary={boundary}',
    'Content-Length': str(len(body_bytes)),
}
conn = http.client.HTTPConnection('127.0.0.1', 8000, timeout=30)
conn.request('POST', '/upload', body_bytes, headers)
resp = conn.getresponse()
resp_text = resp.read().decode(errors='ignore')
print('upload status', resp.status)
print(resp_text)
if resp.status != 200:
    sys.exit(1)
try:
    data = json.loads(resp_text)
    job_id = data.get('job_id')
    print('job_id', job_id)
except Exception as e:
    print('json parse error', e)
    sys.exit(1)
if not job_id:
    print('no job_id returned')
    sys.exit(1)
for i in range(20):
    time.sleep(2)
    conn = http.client.HTTPConnection('127.0.0.1', 8000, timeout=30)
    conn.request('GET', f'/job/{job_id}')
    resp = conn.getresponse()
    body = resp.read().decode(errors='ignore')
    print('poll', i, 'status', resp.status, body)
    if resp.status == 200:
        j = json.loads(body)
        if j.get('status') in ('completed', 'failed'):
            print('final', j)
            break
else:
    print('timeout waiting for job completion')
