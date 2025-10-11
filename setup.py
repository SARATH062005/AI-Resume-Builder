from setuptools import setup, find_packages

setup(
    name='ai-resume-builder',
    version='1.0.0',
    author='Sarath',
    description='An AI-powered resume builder.',
    packages=find_packages(),
    
    # Dependencies are listed directly here.
    # PyQt6 is NOT listed because debian/control handles it via apt.
    install_requires=[
        'Jinja2',
        'requests',
    ],
    
    entry_points={
        'gui_scripts': [
            'ai-resume-builder = main:main',
        ]
    },
    
    # This is important for MANIFEST.in to work
    include_package_data=True,
    zip_safe=False,
)