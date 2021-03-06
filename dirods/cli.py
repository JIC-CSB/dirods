"""Store, retrieve and manage datasets in iRODS."""

import os
import json
import errno
import tempfile
import subprocess

import click
import dtoolcore

dataset_path_option = click.argument(
    'dataset_path',
    type=click.Path(exists=True))


def mkdir_parents(path):
    """Create the given directory path.
    This includes all necessary parent directories. Does not raise an error if
    the directory already exists.
    :param path: path to create
    """

    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


@click.group()
def cli():
    pass


def run_icmd(icmd):
    print(' '.join(icmd))
    subprocess.call(icmd)


def store_in_irods(irods_zone, dataset):

    idataset_basepath = os.path.join(irods_zone, dataset.uuid)
    icmd = ['imkdir', idataset_basepath]
    run_icmd(icmd)

    for identifier in dataset.identifiers:
        source_path = dataset.abspath_from_identifier(identifier)
        dest_path = os.path.join(idataset_basepath, identifier)
        icmd = ['iput', source_path, dest_path]
        run_icmd(icmd)

    manifest_source = dataset._abs_manifest_path
    manifest_dest = os.path.join(idataset_basepath, 'manifest.json')
    icmd = ['iput', manifest_source, manifest_dest]
    run_icmd(icmd)

    admin_metadata = dataset._admin_metadata
    admin_metadata_dest = os.path.join(idataset_basepath, 'dtool')
    fh = tempfile.NamedTemporaryFile()
    fpath = fh.name
    json.dump(admin_metadata, fh)
    fh.flush()
    icmd = ['iput', fpath, admin_metadata_dest]
    run_icmd(icmd)
    fh.close()

    readme_path = dataset.abs_readme_path
    readme_dest = os.path.join(idataset_basepath, 'README.yml')
    icmd = ['iput', readme_path, readme_dest]
    run_icmd(icmd)


@cli.command()
@dataset_path_option
def put(dataset_path):
    dataset = dtoolcore.DataSet.from_path(dataset_path)

    store_in_irods('/jic_archive', dataset)


@cli.command()
@click.argument('uuid')
def get(uuid):

    irods_zone = '/jic_archive'
    idataset_basepath = os.path.join(irods_zone, uuid)

    idtool_path = os.path.join(idataset_basepath, 'dtool')
    icmd = ['iget', idtool_path, '-']
    raw_admin_metadata = subprocess.check_output(icmd)
    admin_metadata = json.loads(raw_admin_metadata)
    dataset_name = admin_metadata['name']

    imanifest_path = os.path.join(idataset_basepath, 'manifest.json')
    icmd = ['iget', imanifest_path, '-']
    raw_manifest = subprocess.check_output(icmd)
    manifest = json.loads(raw_manifest)

    dataset_root_path = dataset_name
    dtool_dir_path = os.path.join(dataset_root_path, '.dtool')
    mkdir_parents(dtool_dir_path)

    dtool_file_path = os.path.join(dtool_dir_path, 'dtool')
    with open(dtool_file_path, 'w') as fh:
        fh.write(raw_admin_metadata)

    manifest_file_path = os.path.join(
        dataset_root_path,
        admin_metadata['manifest_path']
    )
    with open(manifest_file_path, 'w') as fh:
        fh.write(raw_manifest)

    ireadme_path = os.path.join(idataset_basepath, 'README.yml')
    readme_path = os.path.join(
        dataset_root_path,
        admin_metadata['readme_path']
    )
    icmd = ['iget', ireadme_path, readme_path]
    run_icmd(icmd)
    data_root = os.path.join(
        dataset_root_path,
        admin_metadata['manifest_root']
    )
    for entry in manifest['file_list']:
        dest_full_path = os.path.join(data_root, entry['path'])

        if not os.path.exists(dest_full_path):

            dest_path, dest_filename = os.path.split(dest_full_path)

            if len(dest_path):
                mkdir_parents(dest_path)

            ipath = os.path.join(idataset_basepath, entry['hash'])
            icmd = ['iget', ipath, dest_full_path]
            run_icmd(icmd)


@cli.command()
@dataset_path_option
def storemeta(dataset_path):
    dataset = dtoolcore.DataSet.from_path(dataset_path)
    irods_zone = '/jic_archive'
    idataset_basepath = os.path.join(irods_zone, dataset.uuid)

    for k, v, in dataset._admin_metadata.items():
        icmd = ['imeta', 'add', '-C', idataset_basepath, k, v]
        run_icmd(icmd)


@cli.command()
def list():
    irods_zone = '/jic_archive'

    icmd = ['ils', irods_zone]

    results = subprocess.check_output(icmd)

    collection_lines = results.split('\n')[1:-1]

    def getmeta(cpath):
        icmd = ['imeta', 'ls', '-C', cpath, 'name']
        r = subprocess.check_output(icmd)
        value_line = r.split('\n')[2]
        return value_line.split()[1]

    for cl in collection_lines:
        c_path = cl.split()[1]
        uuid = c_path.split('/')[2]
        print(uuid, getmeta(c_path))
