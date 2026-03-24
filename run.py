#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COLLECTOR = ROOT / 'src' / 'collector.py'


def run(cmd):
    print('+', ' '.join(cmd))
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description='总控脚本：历史 BTC/Polymarket 场次重建')
    parser.add_argument('--config', default=str(ROOT / 'config' / 'config.json'))
    parser.add_argument('action', choices=['prepare', 'history', 'export', 'all'])
    args = parser.parse_args()

    base = ['python3', str(COLLECTOR), '--config', args.config]
    if args.action == 'all':
        for step in ('prepare', 'history', 'export'):
            run(base + [step])
    else:
        run(base + [args.action])


if __name__ == '__main__':
    main()
