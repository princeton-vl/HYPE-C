import os
import glob
import random
import string
import tempfile
import boto3
from PIL import Image


def random_name():
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(random.choices(alphabet, k=8))


def upload_anon_images(real_dir,
                       fake_dir,
                       bucket_name,
                       bucket_region='us-east-1',
                       aws_access_key=None,
                       aws_secret_key=None):

    real_filenames = glob.glob(os.path.join(real_dir, '*'))
    fake_filenames = glob.glob(os.path.join(fake_dir, '*'))

    assert(len(real_filenames) > 0)
    assert(len(fake_filenames) > 0)

    kwargs = {}
    kwargs['region_name'] = bucket_region
    if aws_access_key is not None:
        kwargs['aws_access_key_id'] = aws_access_key
    if aws_secret_key is not None:
        kwargs['aws_secret_access_key'] = aws_secret_key

    s3 = boto3.client('s3', **kwargs)

    real_clean = []
    fake_clean = []

    with tempfile.TemporaryDirectory() as tmpdir:

        # Remove all metadata
        def clean_image(filename):
            image = Image.open(filename)
            data = image.getdata()
            clean_image = Image.new(image.mode, image.size)
            clean_image.putdata(data)

            # Check to make sure name not previously used
            collision = True
            while collision:
                clean_name = random_name() + '.png'
                file_check = s3.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix=clean_name
                )
                collision = False
                for obj in file_check.get('Contents', []):
                    if obj['Key'] == clean_name:
                        collision = True
                        break

            clean_image.save(os.path.join(tmpdir, clean_name))

            return clean_name

        for name in real_filenames:
            real_clean.append((name, clean_image(name)))

        for name in fake_filenames:
            fake_clean.append((name, clean_image(name)))

        all_clean = [val[1] for val in real_clean] + [val[1]
                                                      for val in fake_clean]
        random.shuffle(all_clean)

        for name in all_clean:
            success = False
            while not success:
                try:
                    response = s3.upload_file(os.path.join(
                        tmpdir, name), bucket_name, name, ExtraArgs={'ACL': 'public-read'})
                    success = True
                except Exception as e:
                    print(e)

    real_links = [(val[0], "https://{0}.s3.{1}.amazonaws.com/{2}".format(bucket_name,
                                                                         bucket_region,
                                                                         val[1])) for val in real_clean]

    fake_links = [(val[0], "https://{0}.s3.{1}.amazonaws.com/{2}".format(bucket_name,
                                                                         bucket_region,
                                                                         val[1])) for val in fake_clean]

    ret = {"real": real_links, "fake": fake_links}
    return ret
