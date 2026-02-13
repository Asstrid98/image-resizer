from io import BytesIO


def test_health_live(client):
    response = client.get('/health/live')
    assert response.status_code == 200
    assert response.json['status'] == 'alive'


def test_health_ready(client):
    response = client.get('/health/ready')
    assert response.status_code == 200
    assert response.json['status'] == 'ready'


def test_resize_accepted(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '200',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 202
    assert 'job_id' in response.json
    assert response.json['status'] == 'pending'


def test_resize_no_image(client):
    data = {'width': '200', 'height': '200'}
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_resize_invalid_extension(client):
    data = {
        'image': (BytesIO(b'fake'), 'test.txt'),
        'width': '200',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_resize_missing_dimensions(client, sample_image):
    data = {'image': (sample_image, 'test.png')}
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_resize_negative_dimensions(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '-100',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_resize_too_large(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '10000',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_list_jobs_empty(client):
    response = client.get('/jobs')
    assert response.status_code == 200
    assert response.json == []


def test_list_jobs_after_resize(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '100',
        'height': '100'
    }
    client.post('/resize', data=data, content_type='multipart/form-data')
    response = client.get('/jobs')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['status'] == 'pending'


def test_get_job(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '100',
        'height': '100'
    }
    res = client.post('/resize', data=data, content_type='multipart/form-data')
    job_id = res.json['job_id']
    response = client.get(f'/jobs/{job_id}')
    assert response.status_code == 200
    assert response.json['original_filename'] == 'test.png'


def test_get_job_not_found(client):
    response = client.get('/jobs/999')
    assert response.status_code == 404


def test_download_not_completed(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '100',
        'height': '100'
    }
    res = client.post('/resize', data=data, content_type='multipart/form-data')
    job_id = res.json['job_id']
    response = client.get(f'/jobs/{job_id}/download')
    assert response.status_code == 409