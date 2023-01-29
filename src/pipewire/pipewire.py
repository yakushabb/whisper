import signal
from typing import Optional
import subprocess
from time import sleep, time_ns
import re
import threading
from ..utils.async_utils import debounce
from typing import Callable, List, Union


class PwLink():
    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        self.alsa: str = ''
        self.name: str = ''
        self.channels: dict = {}


class PwActiveConnectionLink():
    def __init__(self, tag, channel, _id):
        self.connected_tag: str = tag
        self.channel: str = channel
        self._id: str = _id


class Pipewire():
    def _run(command: List[str]) -> str:
        to_check = command if isinstance(command, str) else ' '.join(command)

        try:
            # print(f'Running {command}')

            output = subprocess.run(['flatpak-spawn', '--host', *command], encoding='utf-8', shell=False, check=True, capture_output=True)
            output.check_returncode()
        except subprocess.CalledProcessError as e:
            print(e.stderr)
            raise e

        return re.sub(r'\n$', '', output.stdout)

    def _parse_pwlink_return(output: str) -> dict[str, PwLink]:
        elements = {}
        resource_tag = None
        line_id = None
        group_line_at = 0

        regex = re.compile(r'^(\s+\d+\s+)')
        for line in output.split('\n'):
            if not line.strip():
                break

            m = regex.match(line)
            if m:
                line_id = m.group().strip()
                resource_tag = (re.sub(f'^{m.group()}', '', line)).split(':', maxsplit=1)[0]

                if not resource_tag in elements:
                    elements[resource_tag] = PwLink(resource_tag)

                group_line_at = 0
                continue

            group_line_at += 1
            line = line.strip()

            if group_line_at == 1:
                elements[resource_tag].alsa = line
            else:
                name, ch = line.split(':')

                elements[resource_tag].name = name
                elements[resource_tag].channels[line_id] = ch

        return elements

    def _parse_pwlink_list_return(output: str) -> [str, dict[str, PwActiveConnectionLink]]:
        elements = {}
        output_id = None

        regex = re.compile(r'^(\s+\d+\s+)')
        conn_regex = re.compile(r'.*(\|\-\>\s*)')
        for line in output.split('\n'):
            if not line.strip():
                break

            m = regex.match(line)
            if ('|->' not in line) and ('|<-' not in line):
                output_id = m.group().strip()
                resource_tag = (re.sub(f'^{m.group()}', '', line)).split(':', maxsplit=1)[0]

                if not output_id in elements:
                    elements[output_id] = {}

                continue

            elif ('|->' in line):
                connection_id = m.group().strip()
                connected_resource = conn_regex.sub('', line)

                _id, connected_item = connected_resource.split(' ', maxsplit=1)
                elements[output_id][connection_id] = PwActiveConnectionLink(connected_item.split(':')[0], connected_item.split(':')[1], _id)

        return elements

    def check_installed() -> bool:
        return Pipewire._run(['which', 'pw-cli']).strip() and Pipewire._run(['which', 'pw-link']).strip() and Pipewire._run(['pw-cli', 'info', '0']).strip()

    def list_inputs() -> dict[str, PwLink]:
        output: list[str] = Pipewire._run(['pw-link', '--input', '--verbose', '--id'])
        inputs = Pipewire._parse_pwlink_return(output)

        return inputs

    def list_outputs() -> dict[str, PwLink]:
        output: list[str] = Pipewire._run(['pw-link', '--output', '--verbose', '--id'])
        items = Pipewire._parse_pwlink_return(output)

        return items

    def link(inp: str, out: str):
        Pipewire._run(['pw-link', '--linger', inp, out])

    def unlink(link_id):
        Pipewire._run(['pw-link', '--disconnect', link_id])

    def list_links() -> [str, dict[str, PwActiveConnectionLink]]:
        return Pipewire._parse_pwlink_list_return(Pipewire._run(['pw-link', '--links', '--id']))

# def threaded_sh(command: Union[str, List[str]], callback: Callable[[str], None]=None, return_stderr=False):
#     to_check = command if isinstance(command, str) else command[0]

#     def run_command(command: str, callback: Callable[[str], None]=None):
#         try:
#             output = sh(command, return_stderr)

#             if callback:
#                 callback(re.sub(r'\n$', '', output))

#         except subprocess.CalledProcessError as e:
#             log(e.stderr)
#             raise e

#     thread = threading.Thread(target=run_command, daemon=True, args=(command, callback, ))
#     thread.start()
