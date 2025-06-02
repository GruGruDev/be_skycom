# -*- mode: Python -*

k8s_yaml([
    'deploy/dev/k8s/local/app.yml',
    'deploy/dev/k8s/local/message_brokers.yml',
    'deploy/dev/k8s/local/redis.yml',
])

k8s_resource(workload='auth-web-deployment', port_forwards='5001:5000')

# Add a live_update rule to our docker_build
docker_build(ref='auth-image', context='./', dockerfile='deploy/dev/Dockerfile',
    live_update=[
        sync('./src', '/home/app'),
        run('cd /home/app && pip install -r requirements.txt',
            trigger='./requirements.txt')
])
