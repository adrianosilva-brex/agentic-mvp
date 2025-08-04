import click
from commands import store, delete, list_files

@click.group()
def cli():
    """CLI tool for managing files in S3"""
    pass

cli.add_command(store)
cli.add_command(delete)
cli.add_command(list_files)

if __name__ == '__main__':
    cli()