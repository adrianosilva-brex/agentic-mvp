import click
from storage.document.main import store_file, delete_file, pretty_list_files
import os   

@click.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--bucket', '-b', default=os.getenv("S3_BUCKET"), help='S3 bucket name')
def store(file_path, bucket):
    """Store a file in the specified S3 bucket"""
    click.echo(f"Storing {file_path} in bucket {bucket}")
    store_file(file_path, bucket)

@click.command()
@click.argument('file_path')
@click.option('--bucket', '-b', default=os.getenv("S3_BUCKET"), help='S3 bucket name')
def delete(file_path, bucket):
    """Delete a file from the specified S3 bucket"""
    click.echo(f"Deleting {file_path} from bucket {bucket}")
    delete_file(file_path, bucket)

@click.command()
@click.option('--bucket', '-b', default=os.getenv("S3_BUCKET"), help='S3 bucket name')
def list_files(bucket):
    """List all files in the specified S3 bucket"""
    click.echo(f"Listing files in bucket {bucket}")
    pretty_list_files(bucket)