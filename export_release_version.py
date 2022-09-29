import shutil
import os


def main():
    release_folder = './albion_regear_bot_release'
    folder = 'regearbot_package'

    shutil.copytree(f'./{folder}', f'{release_folder}/{folder}')

    for file in os.listdir(f'{release_folder}/{folder}'):
        if file == 'config.py':
            os.remove(f'{release_folder}/{folder}/{file}')

    files = ['main.py', 'requirements.txt']
    for file in files:
        shutil.copy(f'./{file}', f'{release_folder}/')


if __name__ == '__main__':
    main()
