
import os
import argparse
from web import create_app

def run(host, port, debug):
    content_dir = os.path.join(os.getcwd(), 'content')
    app = create_app(content_dir)
    app.run(
        host=host,
        port=port,
        debug=debug
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Wiki server app')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Server host')
    parser.add_argument('-p', type=int, default=5000, help='Server port')
    parser.add_argument('-d', type=bool, default=True, help='Debug mode')
    args = parser.parse_args()
    run(args.host, args.p, args.d)