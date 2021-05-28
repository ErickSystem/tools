import os
import re
import subprocess
import sys
import time
import unicodedata

import click
import requests

from ..common.cerebro_api.exceptions import ConnectionError
from ..config import CEREBRO_API
from .enum import SERVICES


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def open_tunnel():
    pem = os.path.join(os.environ.get("HOME"), "aws-keys", "corpusmt.pem")
    if not os.path.isfile(pem):
        click.secho(f"arquivo corpusmt.pem nao encontrado: {pem}", fg="red")
        exit(1)

    tunnel = "ssh -L 0.0.0.0:3307:mutant-corpus-cluster.cluster-ro-cxgxz1hkaric.us-east-1.rds.amazonaws.com:3306  \
              -i ~/aws-keys/corpusmt.pem ec2-user@34.233.116.54 -f -N"

    try:
        stdout, msg = subprocess.getstatusoutput("netstat -lpnt | grep 3307")
        if stdout == 0:
            click.secho("tunnel ja esta aberto!", fg="green")
            click.secho(f"{msg} \n", fg="white")
            pass
        else:
            click.secho("abrindo tunnel...", fg="green")
            subprocess.Popen(tunnel.split())
            time.sleep(5)
    except OSError as e:
        print("falha inesperada no processo: ", e, file=sys.stderr)
        raise

    return None


def pre_process_utterance(s, **kargs):
    """
        Arguments:
        - s {String}
        - lower {bool} -- optional parameter. Used to make the string upper or lower case
    """
    try:
        if isinstance(s, (str)):
            s = s.strip()
            s = re.sub(r"\s{2,}", " ", s)
            s = s.replace("_", " ").replace("\n", "")
            s = re.sub(r"\‘|\’|\“|\”|\'", "", s)
            if "lower" in kargs:
                lower = kargs.get("lower")
                if lower:
                    s = s.lower()
                else:
                    s = s.upper()
    except Exception as e:
        raise ValueError(f"pre process utterance failed beacuse: {str(e)}")

    return str(s)


def abort_if_false(ctx, param, value):
    """ ABORT COMMAND """
    if not value:
        ctx.abort()


def check_service(service):
    """ CHECK SERVICE """
    try:
        k = SERVICES[str(service).upper()]
    except KeyError:
        click.secho(f"servico {str(service).upper()} solicitado nao esta disponivel", fg="red")
        raise

    return k


def remove_special_characters(word):
    """
        The removal of accents was based on a response in the Stack Overflow.
        http://stackoverflow.com/a/517974/3464573
    """

    # Unicode normalize transforms a character to its Latin equivalent.
    nfkd = unicodedata.normalize("NFKD", word)
    word_especialless = "".join([c for c in nfkd if not unicodedata.combining(c)])

    # Use regular expression to return word with numbers, letters and space only
    return re.sub("[^a-zA-Z0-9]", "", word_especialless)


def str2bool(v, param="--enable"):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise click.BadArgumentUsage(f"{param}: value={v} inesperado")


def confirm_access(case_id, user, service):
    """ """
    # if user in ("ericles.lara", "fabio.rezende", "admin", "fabiano.luz", "root"):
    #     return True

    # try:
    #     access = PERMISSION_PROJECT[str(case_id)]
    #     next(u for u in access if u == user)
    # except (Exception, StopIteration, KeyError):
    #     click.secho(
    #         f"[{service}] - usuario {user} nao tem permissao de executar esta acao no projeto {case_id}\n", fg="red"
    #     )
    #     exit(1)

    return True


def find_word_list(s, _list):
    """

    """
    try:
        f = filter(lambda x: x == s, _list)
        result = next(f)
    except StopIteration:
        raise StopIteration("palavra nao encontrada na lista")

    return result


def ping_api():
    URL = f"{CEREBRO_API}/api/_ping"
    params = {}

    try:
        resp = requests.get(url=URL, params=params)
    except Exception:
        raise ConnectionError()

    if resp.status_code != 200:
        raise ConnectionError()
