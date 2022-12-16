from distutils.dir_util import copy_tree


def build_site(notices, files):
    """
    1. Copy base files from assets/docs into root of project
    2. Add files folder, under this is $production.md
    3. Add notices folder, under this is a $yyyy.md
    """
    copy_tree("arcadians_members/assets/mkdocs", "./")
    # with open()
