import setuptools

with open('README.md', 'r', encoding='utf-8') as file:
    long_description = file.read()

setuptools.setup(
    name='git-idiff',
    version='0.0.1',
    author='wilgysef',
    author_email='wilgysef@gmail.com',
    description='An interactive curses tool for viewing git diffs that span multiple files.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/WiLGYSeF/git-idiff',
    project_urls={
        'Bug Tracker': 'https://github.com/WiLGYSeF/git-idiff/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[],
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['git-idiff=git_idiff.__main__:main_args']
    }
)
