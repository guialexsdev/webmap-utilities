# Webmap Utilities - Plugin QGis para facilitar a criação de webmaps

## O que o plugin faz?

O plugin Webmap Utilities oferece ferramentas para facilitar a construção de webmaps, ou seja, mapas dinâmicos cujo conteúdo varia com a escala.

Encorajamos você a usar o sistema de Tags (marcação) proposto pelo projeto (vamos falar disso adiante), mas você pode usar algumas das funcionalidades separadamente se preferir.

Aqui está uma lista de funcionalidades:

* Conjunto de ferramentas para trabalhar com niveis de zoom (0 - 20) ao invés de escalas.
* Você pode atribuir a visibilidade (nivel de zoom) de uma ou várias camadas, até mesmo grupos. 
* O plugin oferece funções para controle de visibilidade, a serem utilizadas nas opções Data Defined Override das camadas. Por exemplo: você pode querer que as cidades de determinada camada apareçam pouco a pouco, conforme o valor de um atributo que indique a população da cidade.
* Oferecermos também funções que controlam campo numéricos (tamanho do rótulo, tamanho do símbolo, transparência). Por exemplo: você pode querer que o tamanho de um rótulo aumente uniformemente entre 7pt a 12pt, conforme o zoom vai aumentando.
* Com o sistema de marcação (tag), fica mais fácil criar templates para reproduzir o conceito de mapas anteriores. Com alguns poucos cliques você pode:
  - Re-organizar suas camadas de acordo com uma organização pré-definida.
  - Aplicar estilos (arquivos QML) para todas as camadas com tag.
  - Download automático de dados OSM de todas as as camadas com tag.

## Requisitos e dependências

* Versão mínima do QGis: 3.28
* É preciso instalar o plugin QuickOSM junto com este plugin.

## Instalação

Por enquanto o projeto está disponível apenas em formato zip. [Clique aqui para baixar o plugin](https://www.trilhasperdidas.com.br/files/plugin/webmap-utilities-plugin.zip).

Para acessar as ferramentas, clique com o botão direito em qualquer área livre da barra de ferramentas (barra de ícones) e marque **Webmap Utilities Toolbar**.

![](/images/toolbar.png)

## Breve Tutorial

O sistema de marcação facilita a replicação e a padronização de mapas. Digamos que você tenha construído um mapa de determinada região e tenha gostado do resultado. Para replicar esse mapa em outra região, apenas alguns clicks seriam necessários para:

* Automaticamente baixar todas as camadas do OSM
* Automaticamente aplicar os estilos para todas as camadas marcadas (camadas vetorias ou raster)
* Automaticamente organizar a árvore de camadas, na ordem correta.

De maneira geral o intuito do sistema de marcação é realizar operações em lote, ou seja, em várias camadas ao mesmo tempo. Com o tempo novas funcionalidades nesse sentido serão publicadas.

Uma tag nada mais é do que uma espécie de categoria, indicando do que se trata determinada camada. Cada tag pode ter uma ou mais propriedades. A tag que representa **cidades**, que é o exemplo que daremos logo adiante, poderá ter uma propriedade chamada **_style**: todas as camadas marcadas com a tag **cidades** receberiam o mesmo estilo. Outra propriedade seria a importante **_zoom_min**, ela indica a partir de qual nivel de zoom as camadas do tipo **cidades** seriam visíveis no mapa.

### Inicializando um projeto

**objetivo**: inicializar o plugin para poder usar as ferramentas que dependem do sistema de tags.

Se você vai utilizar as ferramentas que dependem do sistema de tags, então é preciso inicializar o projeto. Para isso, clique no botão ![](/images/configure_project.png). Esse primeiro passo é necessário, já que os niveis de zoom, principalmente se você pretende fazer mapas para visualizar em aplicativos ou no leaflet, precisam estar configurados para escalas específicas. Além disso, ao inicializar o projeto, o plugin salvará as configurações padrão. 

Só é preciso incializar o projeto uma vez, desde que você sempre salve o projeto. E uma vez inicializado, todos os botões do plugin serão liberados, como na imagem abaixo.

![](/images/toolbar_only.png)

Lembre-se que para acessar essas ferramentas, é preciso clicar com o botão direito em qualquer área livre da barra de ferramentas (barra de ícones) e marcar a opção **Webmap Utilities Toolbar**, para adicionar o plugin na barra de ícones.

### Adicionando tags

**objetivo**: marcar algumas das nossas camadas com um tag.

O sistema de tags é simples. Primeiro você define em qual categoria cairá cada camada. Por exemplo, suponha que você tenha várias camadas de pontos, de diferentes fontes, representando as **cidades** de determinada região. Embora possam ter diferentes nomes e até features diferentes, todas essas camadas podem ser classificadas como sendo de um mesmo tipo, de uma mesma TAG, chamada **cidade**.

Em seguida, precisamos planejar como o plugin irá reconhecer a tag de uma camada. Atualmente isso pode ser feito de 2 formas:

* Colocando logo no início do nome da camada a TAG escolhida. Por exemplo, nossas camadas de cidades podem ser nomeadas por **cidades fonte1** e **cidades fonte2**.
* Ou então é possível apenas inserir a TAG nos metadados da cama. Basta ir em Propriedades -> Metadados -> Categorias e inserir lá a tag escolhida.

Agora vá em ![](/images/settings.png) **Settings** e registre a tag clicando no botão ![](/images/symbologyAdd.png) **Add new tag...**. Não esqueça de selecionar, no seletor da parte inferior da tela, o modo de identificação das tags!

![](/images/step_adding_tag.png)

### Adicionando uma propriedade à TAG

**objetivo**: adicionar uma propriedade à nossa tag. Posteriormente essa propriedade controlará em qual nivel de zoom as camada com a nossa tag estarão visíveis no mapa.

O próximo passo é inserir algumas propriedades à tag recém criada. Propriedade é uma espécie de parâmetro para controlar alguma coisa do mapa. Por exemplo, por padrão existem as propriedades `_zoom_min` e `_zoom_max`. Elas controlam o intervalo de zoom em que sua camada será visível. Se você coloca, digamos, o valor 9 para `_zoom_min` e 10 para `_zoom_max`, isso significa que todas as features da camada serão vistas apenas nesse intervalo. Essas propriedades são globais: todas as features da sua camadas vão obedecer esses valores. Mas você pode querer que uma ou outra feature esteja visivel, por exemplo, entre o intervalo de zoom 8 e 16. Nesse caso, você pode criar `_zoom_min` e `_zoom_max` como se fossem atributos da sua camada. O plugin dará preferência aos valores individuais de cada feature.

Para adicionar uma propriedade à tag, vá em ![](/images/settings.png) **Settings** -> Tags e clique com o botão direito no nome da tag. No menu, cloque em **Add Property...**. Selecione `_zoom_min`, coloque o número 9 e dê OK. Repita o procedimento para `_zoom_max`, mas colocando o valor 15 dessa vez. A ideia é que a nossa camada de cidades fique visível apenas entre o zoom 9 e 15. Mas você ainda não verá isso acontecer. Uma próxima etapada ainda é necessária.

![](/images/step_add_property.png)

Você pode criar suas propriedades caso necessário. Na tela, basta cadastrá-las na tela ![](/images/settings.png) **Settings** -> Properties. Lá será possível escolher o tipo de propriedade (texto, numérico etc), ou se terá uma lista de valores associada.

**Outras propriedades úteis**

- `_style`: essa propriedade especifica qual estilo será automaticamente atribuído às camadas daquela tag. Vá em [Aplicando estilos automaticamente](#aplicando-estilos-automaticamente) para entender melhor.
- `_osm_query`: Chaves e valor para a pesquisa OSM. Ex: place=city, highway=primaryetc. Vá em [Baixando camadas vetoriais OSM](#baixando-camadas-vetoriais-osm) para entender melhor.
- `_geometry_type`: Tipo de camada vetorial que a tag representa. Opções: points, lines, multilines to multipolygons.

### Controlando uma camada vetorial

**objetivo**: tornar as camadas (marcadas com a nossa tag) visíveis ou não em cada nivel de zoom. No primeiro exemplo, faremos todas as feature da camada serem visíveis a partir de `_zoom_min`. Depois faremos as feature aparecerem aos poucos, quanto maior a população, mais 'cedo' aparecerá a cidade.

Abra as propriedades da camada para trabalharmos com rótulos. Crie um estilo básico qualquer. Depois vá para seção **Show Label**, em **Data defined override** e depois clique em editar. O que vamos fazer aqui é adicionar um controle de visibilidade através de funções que o plugin oferece. Essas funções é que utilizam algumas das propriedades da tag, como a nossas já estudadas `_zoom_min` e `_zoom_max`.

![](/images/step_controlling_layer1.png)

Todas as funções oferecidas pelo plugin estão sob as opções 'Webmap - General' e 'Webmap - Visibility'. Assim sendo, digite seguinte fórmula:

```
controlVisibility()
```

Clique em Aplicar e saia da tela de propriedades da camada e volte ao canvas. Vá navegando, aproximando e afastando o zoom e verifique que nossa camada estará visível apenas no intervalo definido pelas propriedades discutos no passo anterior. Lembre-se que você pode criar atributos com o mesmo nome dessas propriedades e colocar intervalos diferentes, mas que só serão aplicados para aquela featura específica.

Agora vamos usar outra função de visibilidade, mas dessa vez uma que funciona com os tais Percentis. É uma forma de apresentar a camada aos poucos. A cada zoom, mais 5% das cidades mais populosas vão aparecendo. Ou seja, no início 5% das cidades com maior população vão aparecer. No próximo nivel de zoom, 15% das cidades mais populosas vão aparecer... e assim por diante. Esses valores em porcentagem são os percentis.

Aqui está a função que controla a visibilidade por percentil:

```
controlVisibilityByPercentilesIncrement('population', 5, 10)
```

Explicando os argumentos:

* 1º parametro: nome do atributos a ser considerado nos cálculos (seria o campo que conteria a população das cidades, no nosso exemplo).
* 2º parametro: Percentil mínimo (5%, no nosso exemplo)
* 3º parametro: Incremento, por zoom, ao percentil mínimo (a partir de 5%, crescendo de 10% em 10%).

### Aplicando estilos automaticamente

Toda vez que você clica em no ícone ![](/images/apply_style.png). os estilos cadastrados em cada tag serão aplicados. Qual estilo será aplicado, dependerá do que for especificado na propriedade `_style` de cada tag. Funciona para qualquer tipo de camada, desde que tenha uma TAG associada.

### Estrutura: re-organizando automaticamente as camadas

Parte do problema de quem produz mapas em série é padronizar inclusive a ordem em que as camadas aparecem dentro do Qgis. Com o tempo é comum que as diferenças entre um projeto e outro apareçam. A ferramenta **Apply Structure** Quando terminar, vá em **Settings -> Structure**, clique em **Update** e depois em **Apply**. A estrutura de pastas (grupos) e a ordem das camadas COM TAG serão gravadas. A partir de então, toda vez que você clicar no ícone ![](/images/apply_structure.png), o projeto será automaticamente organizado, na mesma ordem e nas mesmas pastas (mesmo que não estejam criadas).

### Baixando camadas vetoriais OSM

Você pode adicionar uma propriedade OSM à suas tags de forma que o plugin consiga automaticamente baixar as camadas vetoriais. Para isso, atribua à suas tags as propriedades `_osm_query` e `_geometry_type`. Veja o que são essqas propriedades:

* `_osm_query`: chave e valor de pesquisa. No formato: chave=valor. Apenas um valor por entrada na lista apresentada na tela de adição de propriedade. Por exemplo, para obter as cidades adicionaríamos o seguinte (2 entradas diferentes): 
- place=city
- place=town

* `_geometry_type`: tipo de geometria. Valores possíves: points, lines, multilinestrings e multipolygons. No caso do nosso exemplo anterior, a escolha seria 'points', já que cidades são entidades pontuais (pelo menos assim costuma-se representar no mapa).

Para baixar automaticamente os dados OSM de todas as tags, basta clicar em ![](/images/osm.png), selecionar o CRS e a extensão. Há um outro campo onde você pode selecionar as tags a serem baixadas: por padrão, todas são selecionadas... mas caso já tenha baixado alguma, basta selecionar ou des-selecionar as tags antes de executar.

### Gerando Sombreamento

A ferramenta de sombreamento oferecida pelo plugin baseia-se em 2 técnicas:

* **Iluminação bidirecional**: duas fontes de luz são usadas. Isso garante que mais de um lado de uma montanha seja iluminado, revelando detalhes que de outra maneira estariam encobertos por sombras. Não usamos mais do que uma fonte de luz pois isso frequentemente gera sombreamentos pouco naturais, muitas vezes plastificados. Você controla o ângulo entre essas fontes através do campo **Angle between light sources**. O valor ideal para esse parâmetro é algo entre 35 - 70 graus. Valores menores tendem a criar duas fontes de luz muito próximas e o efeito acaba sendo pequeno. Valores maiores tendem a dar resultados mais plastificados.

* **Perspectiva Aérea**: sombreamentos são excelentes peças para dar ao leitor do mapa uma visão clara do relevo. Mas podem atrapalhar muito conforme outros elementos vão sendo inseridos: as cidades, as estradas, rótulos etc. O culpado disso muitas vezes é o contraste imposto pelas sombras e luzes do sombreamento. A persectiva aérea ameniza esse problema ao diminuir o contraste nas áreas mais baixas e aumentá-lo nas mais altas. Isso é bom porque justamente em regiões mais baixas é que em geral temos grande acúmulo de elementos urbanos e, portanto, de simbologias e rótulos. Já no alto das montanhas não costumamos ter muitos elementos representados, podendo dar-se ao luxo de ter bom contraste. Controle a perspectiva aérea através do parâmetro **Aerial Perspective Intensity**. Quanto mais alto o valor, maior a diferença de contraste entre as regiões altas e baixas. Valores entre 50 e 70 costumam dar bons resultados. Saiba mais sobre esse tema em: http://www.reliefshading.com/design/aerial-perspective/.

Importante ressaltar que essa ferramenta gera 2 camadas que precisam estar na ordem em que são geradas. Renomei-as, se necessário, para lembrar a ordem. O motivo disso é que cada camada representa uma das fontes de luz e ainda recebem diferentes configurações de brilho, contraste e transparência. 

Por último, lembre-se de deixar o DEM debaixo das duas camadas, colorindo-o conforme achar melhor.

Clique em ![](/images/relief_creator.png) para gerar o sombreamento.


### Outras funcionalidades

* Ao invés de usar o seletor de escalas, aquele que fica na parte inferior da tela, você pode usar o seletor de niveis de zoom, que fica ao lados dos ícones da barra nossa barra de ferramentas.
* Existem duas maneiras de adicionar e editar tags. Você acessar a opção ![](/images/settings.png) **Settings** e lá escolher a aba Tag ou Properties; ou então pode clicar com o botão direito em qualquer camada com tag e escolher as opções de **Set tag property...**.
* Você pode criar as próprias propriedades. Lá em ![](/images/settings.png) **Settings** é só abrir a aba **Properties** e cadastrar. Após isso, ela estará disponível para uso na aba **Tags**.
* Para replicar as mesmas configurações, tags e propriedades em outro projeto você pode:
   - Exportar e Importar (há opções para isso em ![](/images/settings.png) **Settings**)
   - Ou criar um Projeto Template no Qgis (e nada mais, já que todas as configurações são guardadas no projeto)

## Projeto Exemplo

No link abaixo você poderá fazer o download de um projeto exemplo. É um arquivo `.wpc`, ou seja, um arquivo de exportação do plugin. Basta iniciar um projeto no Qgis, inicializar o plugin, ir em ![](/images/settings.png) **Settings** e clicar em **Import**. Você será perguntado se quer sobreescrever as configurações atuais, diga que sim. Depois será perguntado se quer salvar em uma pasta específica os estilos embutidos no arquivo de exportação ou se deseja usar como arquivo temporário. Clique na opção **Use a temporary folder** por enquanto, apenas para ter uma ideia de como funciona o plugin.

[Clique aqui para baixar o projeto de exemplo](https://www.trilhasperdidas.com.br/files/plugin/webmap_plugin_example.wpc)

O estilo do arquivo DEM pode ficar bom ou não, a depender da região. Mas aqui vai um DEM de exemplo, de Santiago - Chile, que usamos originalmente: [Clique aqui para baixar o arquivo DEM de exemplo](https://www.trilhasperdidas.com.br/files/plugin/dem_santiago.wpc). Mas você pode usar o seu próprio DEM. Lembre-se que nesse projeto exemplo usamos unicamente os dados OSM, então a região que você escolher pode ou não ter dados suficientes. Tente escolher um local com cidades um pouco maiores para aumentar as chances de ter dados suficientes no OSM.