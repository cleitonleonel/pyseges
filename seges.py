import os
import sys
import tempfile
import requests
import webbrowser
from bs4 import BeautifulSoup

BASE_URL = 'https://segespais.caedufjf.net'

html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Boletim Escolar</title>
  <link href="%(base_url)s/seges/bootstrap/css/bootstrap.min.css" rel="stylesheet" type="text/css" />
  <link href="%(base_url)s/seges/css/fixBootstrap.css" rel="stylesheet" type="text/css" />
</head>
<style>
html, body {margin: 0; height: 100; overflow: hidden}
.container {
    height: 100vh;
    display: flex;
    flex-direction: row;
    justify-content: center;
    align-items: center;
}
.box {
    width: 300px;
    height: 300px;
    background: #fff;
}
body {
    margin: 0px;
}
</style>
<body>
    <h3 style="text-align:center">Aluno: %(studant)s</h3>
    <div class="container">
    %(body)s
    </div>
</body>
</html>
"""


class Browser(object):

    def __init__(self):
        self.response = None
        self.current_page = 1
        self.headers = self.get_headers()
        self.session = requests.Session()

    def get_headers(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/87.0.4280.88 Safari/537.36"
        }
        return self.headers

    def send_request(self, method, url, **kwargs):
        requests.packages.urllib3.disable_warnings()
        self.response = self.session.request(method, url, **kwargs)
        return self.response

    def get_soup(self):
        return BeautifulSoup(self.response.text, "html.parser")


class SegesAPI(Browser):

    def __init__(self, username=None, password=None):
        super().__init__()
        self.username = username
        self.password = password
        self.selected = None
        self.access_login = None
        self.view_state = None
        self.registration = None
        self.student = None
        if not self.username or not self.password:
            print("Erro, usuário e senha inválidos ou não inseridos.")
            print("Entre com seu usuário e senha...")
            sys.exit()

    def auth(self):
        self.send_request('GET', f'{BASE_URL}/seges/login.faces', headers=self.headers)

        data = {
            "formulario": "formulario",
            "formulario:login": self.username,
            "formulario:senha": self.password,
            "formulario:logar": "",
            "javax.faces.ViewState": self.get_soup().find("form").find("input", {
                "name": "javax.faces.ViewState"})["value"]
        }

        self.headers["Host"] = "segespais.caedufjf.net"
        self.headers["Origin"] = BASE_URL
        self.headers["Referer"] = f"{BASE_URL}/seges/inicio.faces"

        self.send_request('POST', f'{BASE_URL}/seges/login.faces', headers=self.headers, data=data)
        if "/seges/novo/login/selecaoPerfil.faces" in self.get_soup().find_all("form")[0]["action"]:
            return self.is_father()
        message = self.get_soup().find("tr", {"class": "alturaTotal"})
        if message:
            print(message.find_all("td")[1].text)
            return False
        return self.select_menu()

    def is_father(self):
        self.access_login = self.get_soup(
        ).find_all("form")[0].find("select").find_all("option")[1]["value"]

        self.view_state = self.get_soup().find_all("form")[0].find("input", {
            "name": "javax.faces.ViewState"})["value"]
        data = {
            "AJAXREQUEST": "regionConteudo",
            "formulario": "formulario",
            "formulario:instituicaoLogin": "Selecione a opção",
            "formulario:alunoLogin": "Selecione a opção",
            "javax.faces.ViewState": self.view_state,
            "formulario:grupoAcessoLogin": self.access_login,
            "formulario:j_id11": "formulario:j_id11",
            "ajaxSingle": "formulario:grupoAcessoLogin"
        }

        self.headers["Host"] = "segespais.caedufjf.net"
        self.headers["Origin"] = BASE_URL
        self.headers["Referer"] = f"{BASE_URL}/seges/novo/login/selecaoPerfil.faces"

        self.send_request('POST',
                          f'{BASE_URL}/seges/novo/login/selecaoPerfil.faces',
                          headers=self.headers,
                          data=data)
        options = self.get_soup().find_all("div", {"class": "span12"})[1].find("select").find_all("option")[1:]
        select = 0
        if len(options) > 1:
            print("Os seguintes usuários foram encontrados: ")
            for index, option in enumerate(options):
                print(index, option.text)
            select = int(input("Digite o número correspondente a opção desejada: "))
            self.student = options[select].text
        self.selected = options[select]["value"]
        return self.continue_father_login()

    def continue_father_login(self):
        data = {
            "AJAXREQUEST": "regionConteudo",
            "formulario": "formulario",
            "formulario:instituicaoLogin": "Selecione a opção",
            "formulario:alunoLogin": self.selected,
            "formulario:matriculaLogin": "Selecione a opção",
            "formulario:grupoAcessoLogin": self.access_login,
            "javax.faces.ViewState": self.view_state,
            "formulario:j_id21": "formulario:j_id21",
        }

        self.headers["Host"] = "segespais.caedufjf.net"
        self.headers["Origin"] = BASE_URL
        self.headers["Referer"] = f"{BASE_URL}/seges/novo/login/selecaoPerfil.faces"

        self.send_request('POST',
                          f'{BASE_URL}/seges/novo/login/selecaoPerfil.faces',
                          headers=self.headers,
                          data=data)

        return self.persistent_father_login()

    def persistent_father_login(self):
        self.registration = self.get_soup().find_all("div", {
            "class": "span12"})[2].find("select").find_all("option")[1:]
        select = 0
        if len(self.registration) > 1:
            print("Os seguintes boletins foram encontrados: ")
            for index, option in enumerate(self.registration):
                print(index, option.text)
            select = int(input("Digite o número correspondente a opção desejada: "))
            self.registration = self.registration[select]["value"]

            data = {
                "AJAXREQUEST": "regionConteudo",
                "formulario": "formulario",
                "formulario:instituicaoLogin": "Selecione a opção",
                "formulario:alunoLogin": self.selected,
                "formulario:matriculaLogin": self.registration,
                "formulario:grupoAcessoLogin": self.access_login,
                "javax.faces.ViewState": self.view_state,
                "formulario:j_id25": "formulario:j_id25",
            }

            self.headers["Host"] = "segespais.caedufjf.net"
            self.headers["Origin"] = BASE_URL
            self.headers["Referer"] = f"{BASE_URL}/seges/novo/login/selecaoPerfil.faces"

            self.send_request('POST',
                              f'{BASE_URL}/seges/novo/login/selecaoPerfil.faces',
                              headers=self.headers,
                              data=data)
        else:
            self.registration = self.registration[select]["value"]

        data = {
            "AJAXREQUEST": "regionConteudo",
            "formulario": "formulario",
            "formulario:instituicaoLogin": "Selecione a opção",
            "formulario:alunoLogin": self.selected,
            "formulario:matriculaLogin": self.registration,
            "formulario:grupoAcessoLogin": self.access_login,
            "javax.faces.ViewState": self.view_state,
            "formulario:selecionar": "formulario:selecionar"
        }

        self.headers["Host"] = "segespais.caedufjf.net"
        self.headers["Origin"] = BASE_URL
        self.headers["Referer"] = f"{BASE_URL}/seges/novo/login/selecaoPerfil.faces"

        self.send_request('POST',
                          f'{BASE_URL}/seges/novo/login/selecaoPerfil.faces',
                          headers=self.headers,
                          data=data)

        action_redirect = self.get_soup().find_all("meta")[1]["content"]

        self.send_request('GET',
                          f'{BASE_URL}{action_redirect}',
                          headers=self.headers)

        return self.select_menu()

    def select_menu(self):
        data = {}
        for input_tag in self.get_soup().find_all("form")[1].find_all("input"):
            data[input_tag["name"]] = input_tag["value"] if input_tag.get("value") else ""

        data["panelMenuStateformMenu:ACESSO_PAIS_RENDIMENTO_ESCOLAR_2"] = "opened"
        data["panelMenuActionformMenu:ACESSO_PAIS_BOLETIM_2"] = "formMenu:ACESSO_PAIS_BOLETIM_2"
        data["formMenu:panelMenuselectedItemName"] = "ACESSO_PAIS_BOLETIM_2"

        self.headers = self.get_headers()
        self.headers["Host"] = "segespais.caedufjf.net"
        self.headers["Origin"] = BASE_URL
        self.headers["Referer"] = f"{BASE_URL}/seges/inicio.faces"

        self.send_request('POST',
                          f'{BASE_URL}/seges/inicio.faces',
                          headers=self.headers,
                          data=data)
        return self.prepare_view()

    def prepare_view(self):
        self.headers = self.get_headers()
        self.headers["Host"] = "segespais.caedufjf.net"

        self.send_request('GET',
                          f'{BASE_URL}/seges/novo/acessoPais/telaAcessoPais.faces',
                          headers=self.headers)
        return self.get_view_page()

    def get_view_page(self):
        self.student = self.get_soup().find("span", {"style": "padding-left: 5px;"}).text \
            if not self.student else self.student
        data = {"AJAXREQUEST": "regionConteudo"}
        for input_tag in self.get_soup().find_all("form")[1].find_all("input"):
            data[input_tag["name"]] = input_tag["value"]
        data["formulario:verBoletim"] = "formulario:verBoletim"

        self.headers = self.get_headers()
        self.headers["Host"] = "segespais.caedufjf.net"
        self.headers["Origin"] = BASE_URL
        self.headers["Referer"] = f"{BASE_URL}/seges/novo/acessoPais/telaAcessoPais.faces"

        self.send_request('POST',
                          f'{BASE_URL}/seges/novo/acessoPais/telaAcessoPais.faces',
                          headers=self.headers,
                          data=data)

        if self.get_soup().find("div", {"id": "formulario:tabelaResultados"}):
            return True
        return False

    def wiew_page(self):
        soup = self.get_soup()
        div_tag = soup.find("div", {"class": "span12"}).prettify()

        result_dict = {
            "studant": self.student,
            "body": div_tag,
            "base_url": BASE_URL
        }

        page = html % result_dict

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'boletim.html')
            with open(temp_file_path, 'w') as fh:
                fh.write(page)
            webbrowser.open('file://' + temp_file_path)


if __name__ == "__main__":
    sa = SegesAPI("user", "senha")
    if sa.auth():
        sa.wiew_page()
