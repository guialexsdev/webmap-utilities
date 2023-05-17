# Webmap Utilities - Plugin QGis para facilitar a criação de webmaps

## O que o plugin faz:

O plugin Webmap Utilities oferece ferramentas para facilitar a construção de webmaps, ou seja, mapas dinâmicos cujo conteúdo varia com a escala.

Encorajamos você a usar o sistema de Tags (marcação) proposto pelo projeto (vamos falar disso adiante), mas você pode usar algumas das funcionalidades separadamente se preferir.

Aqui está uma lista de funcionalidades:

* Conjunto de ferramentas para trabalhar com niveis de zoom (0 - 20) ao invés de escalas.
* Você pode atribuir a visibilidade (nivel de zoom) de uma ou várias camadas (até mesmo grupos). 
* O plugin oferece funções para controle de visibilidade, a serem utilizadas nas opções Data Defined Override das camadas. Por exemplo: você pode querer que as cidades de determinada camada apareçam pouco a pouco, conforme o valor de um atributo que indique a população da cidade.
* Oferecermos também funções que controlam campo numéricos (tamanho do rótulo, tamanho do símbolo, transparência). Por exemplo> você pode querer que o tamanho de um rótulo aumente uniformemente entre 7pt a 12pt, conforme o zoom vai aumentando.
* Com o sistema de marcação (tag), fica mais fácil criar templates de reproduzir o conceito de mapas anteriores. Com alguns poucos cliques você pode:
  - Re-organizar suas camadas de acordo com uma organização pré-definida.
  - Aplicar estilos (arquivos QML) para todas as camadas com tag.
  - Download automático de dados OSM de todas as as camadas com tag.

## Requisitos e dependências

* Versão mínima do QGis: 3.28
* É preciso instalar o plugin QuickOSM junto com este plugin.

## Instalação

No QGis, instale o Webmap Utilities através do menu **Plugins -> Manage and Install Plugins**. Procure por Webmap Utitlities" e instale. Pode ser necessário, na aba Settings do gerenciador de plugins, marcar a opção **Show also Experimental Plugins**.

Para acessar as ferramentas, clique com o botão direito em qualquer área livre da barra de ferramentas (barra de ícones) e marque **Webmap Utilities Toolbar**.

## Breve Tutorial

O sistema de marcação facilita a replicação e a padronização de mapas. Digamos que você tenha construído um mapa de determinada região e tenha gostado do resultado. Para replicar esse mapa, mas para outra região, apenas alguns clicks seriam necessários para:

* Automaticamente baixar todas as camadas do OSM
* Automaticamente aplicar os estilos para todas as camadas marcadas (camadas vetorias ou raster)
* Automaticamente organizar a árvore de camadas, na ordem correta.

### Adicionando tags

O sistema de tags é simples. Primeiro você define em qual categoria cai cada camada. Por exemplo, suponha que você tenha várias camadas de pontos, de diferentes fontes, representando as **cidades** de determinada região. Embora possam ter diferentes nomes e até features diferentes, todas essas camadas podem ser classificadas como sendo de um mesmo tipo, de uma mesma TAG, chamada **cidade**.

Em seguida, precisamos planejar como o plugin irá reconhecer a tag de uma camada. Atualmente isso pode ser feito de 2 formas:

* Colocando logo no início do nome da camada a TAG escolhida. Por exemplo, nossas camadas de cidades podem ser nomeadas por **cidades fonte1** e **cidades fonte2**.
* Ou então é possível apenas inserir a TAG nos metadados da cama. Basta ir em Propriedades -> Metadados -> Categorias e inserir lá a tag escolhida.

Agora vá em ![](/images/settings.png) **Settings** e registre a tag clicando no botão ![](/images/symbologyAdd.png) **Add new tag...**. Não esqueça de selecionar, no seletor da parte inferior da tela, o modo de identificação das tags!

![](/images/step_adding_tag.png)

### Adicionando uma propriedade à TAG

O próximo passo é inserir algumas propriedades à tag recém criada. Propriedade é uma espécie de parâmetro para controlar alguma coisa do mapa. Por exemplo, por padrão existem as propriedades `_zoom_min` e `_zoom_max`. Elas controlam o intervalo de zoom em que sua camada será visível. Se você coloca, digamos, o valor 9 para `_zoom_min` e 10 para `_zoom_max`, isso significa que todas as features da camada serão vistas apenas nesse intervalo. Essas propriedades são globais: todas as features da sua camadas vão obedecer esses valores. Mas você pode querer que uma ou outra feature esteja visivel, por exemplo, entre o intervalo de zoom 8 e 16. Nesse caso, você pode criar `_zoom_min` e `_zoom_max` como se fossem atributos da sua camada. O plugin dará preferência aos valores individuais de cada feature.

Para adicionar uma propriedade à tag, vá em ![](/images/settings.png) **Settings** -> Tags e clique com o botão direito no nome da tag. No menu, cloque em **Add Property...**. Selecione `_zoom_min`, coloque o número 9 e dê OK. Repita o procedimento para `_zoom_max`, mas colocando o valor 15 dessa vez. A ideia é que a nossa camada de cidades fique visível apenas entre o zoom 9 e 15. Mas você ainda não verá isso acontecer. Uma próxima etapada ainda é necessária.

![](/images/step_add_property.png)

**Outras propriedades úteis**

- `_style`: essa propriedade especifica qual estilo será automaticamente atribuído às camadas daquela tag. Vá em [Aplicando estilos automaticamente](#aplicando-estilos-automaticamente) para entender melhor.
- `_osm_key`: Chave de pesquisa OSM. Ex: place, highway, waterway etc. Precisa co-existir com as outras propriedades OSM. Vá em [Baixando camadas vetoriais OSM](#baixando-camadas-vetoriais-osm) para entender melhor.
- `_osm_value`: Junto com `_osm_key`, elas formam 'consulta' para baixar dados OSM. Ex: town, primary_roads, river etc. Precisa co-existir com as outras propriedades OSM.Vá em [Baixando camadas vetoriais OSM](#baixando-camadas-vetoriais-osm) para entender melhor.
- `_osm_type`: Tipo de camada a ser baixada do OSM. Opções: points, lines, multilines to multipolygons. Precisa co-existir com as outras propriedades OSM.Vá em [Baixando camadas vetoriais OSM](#baixando-camadas-vetoriais-osm) para entender melhor.

### Controlando uma camada vetorial

Abra as propriedades da camada. Vamos trabalhar com rótulos. Antes de tudo, crie um estilo básico qualquer. Depois vá para seção **Show Label**, em **Data defined override** e depois clique em editar. O que vamos fazer aqui é adicionar um controle de visibilidade através de funções que o plugin oferece. Essas funções é que utilizam algumas das propriedades da tag, como a nossas já estudadas `_zoom_min` e `_zoom_max`.

![](/images/step_controlling_layer1.png)

Todas as funções oferecidas pelo plugin estão sob as opções 'Webmap - General' e 'Webmap - Visibility'. Assim sendo, digite seguinte fórmula:

```
controlVisibility(@zoom_level)
```

Clique em Aplicar e saia da tela de propriedades da camada e volte ao canvas. Vá navegando, aproximando e afastando o zoom e verifique que nossa camada estará visível apenas no intervalo definido pelas propriedades discutos no passo anterior. Lembre-se que você pode criar atributos com o mesmo nome dessas propriedades e colocar intervalos diferentes, mas que só serão aplicados para aquela featura específica.

Agora vamos usar outra função de visibilidade, mas dessa vez uma que funciona com os tais Percentis. É uma forma de apresentar a camada aos poucos. A cada zoom, mais 5% das cidades mais populosas vão aparecendo. Ou seja, no início 5% das cidades com maior população vão aparecer. No próximo nivel de zoom, 15% das cidades mais populosas vão aparecer... e assim por diante. Esses valores em porcentagem são os percentis.

Aqui está a função que controla a visibilidade por percentil:

```
controlVisibilityByPercentilesIncrement(@zoom_level, 'population', 5, 10)
```

Explicando os argumentos:

* 1º parametro: nivel de zoom atual.
* 2º parametro: nome do atributos a ser considerado nos cálculos (seria o campo que conteria a população das cidades, no nosso exemplo).
* 3º parametro: Percentil mínimo (5%, no nosso exemplo)
* 4º parametro: Incremento, por zoom, ao percentil mínimo (a partir de 5%, crescendo de 10% em 10%).

### Aplicando estilos automaticamente

Toda vez que você clica em no ícone ![](/images/apply_style.png). os estilos cadastrados em cada tag serão aplicados. Qual estilo será aplicado, dependerá do que for especificado na propriedade `_style` de cada tag.

### Estrutura: re-organizando automaticamente as camadas

Após definir como será a estrutura de camadas do seu projeto, vá em **Settings -> Structure**, clique em **Update** e depois em **Apply**. A organização das camadas com tag será gravada. A partir de então, toda vez que você clicar no ícone ![](/images/apply_structure.png), o projeto será automaticamente organizado, na mesma ordem.

### Baixando camadas vetoriais OSM

Você pode adicionar propriedades OSM à suas tags de forma que o plugin consiga automaticamente baixar as camadas OSM correspondentes. Para isso, atribua à suas tags as propriedades `_osm_key`, `_osm_values` e `_osm_type`. No caso da propriedade `_osm_values`, é possível adicionar mais de um valor.

Por exemplo, uma possível configuração para baixar rodovias seria:

* `_osm_key` = highway
* `_osm_values` ​​= [primary, secondary, tertiary]
* `_osm_type` = lines

Para baixar automaticamente os dados OSM de todas as tags, basta clicar em ![](/images/osm.png), selecionar o CRS e a extensão. Tenha em mente que só serão baixadas as camadas com tag que possuam todas as três propriedades acima mencionadas.

### Gerando Sombreamento

O plugin gera 2 camadas raster de sombreamento, já na ordem em que precisam estar: uma em cima da outra. Precisa ser assim porque usamos duas fontes luminosas, com diferentes azimutes, blend modes e configurações de brilho e contraste. Essa composição dá ao sombramento final mais detalhes e mais suavidade.

Além disso, as duas camadas recebem o efeito de Perspectiva Aérea: quanto mais alto, mais contraste. Isso é bom porque em geral as porções mais baixas de determinada regiões é que contém a maior quantidade de cidades, vilas, estradas, estabelecimentos etc... e menos constraste significa maior facilidade para ler o mapa quando há muitos elementos sobre ele. Caso queira, aqui está um bom artigo sobre esse tema: http://www.reliefshading.com/design/aerial-perspective/.=

Clique em ![](/images/relief_creator.png) para gerar o sombreamento.


### Outras funcionalidades

* Ao invés de usar o seletor de escalas, aquele que fica na parte inferior da tela, você pode usar o seletor de niveis de zoom, que fica ao lados dos ícones da barra nossa barra de ferramentas.
* Existem duas maneiras de adicionar e editar tags. Você acessar a opção ![](/images/settings.png) **Settings** e lá escolher a aba Tag ou Properties; ou então pode clicar com o botão direito em qualquer camada com tag e escolher as opções de **Set tag property...**.
* Você pode criar as próprias propriedades. Lá em ![](/images/settings.png) **Settings** é só abrir a aba **Properties** e cadastrar. Após isso, ela estará disponível para uso na aba **Tags**.
* Para replicar as mesmas configurações, tags e propriedades em outro projeto você pode:
   - Exportar e Importar (há opções para isso em ![](/images/settings.png) **Settings**)
   - Ou criar um Projeto Template no Qgis (e nada mais, já que todas as configurações são guardadas no projeto)
