import sys
sys.path.insert(0, '.')
exec(open('script/scraper_volantino_latest.py').read().replace('if __name__ == "__main__":', 'if False:').replace('else:', 'if True:') + "\nmain()")