# Webmap Utilities - Um plugin QGis para auxiliar a construção de webmaps

Este plugin oferece ferramentas para auxiliar na construção de mapas dinâmicos, webmaps. Aqui está uma lista de funcionalidades:

- Mecanismos de visualização de camadas vetoriais baseado em niveis de zoom, clusters e grids.
- Aplicação da técnica chamada Perspectiva Aérea, para amenizar os constrastes de uma camada de Sombreamento.
- Criação de uma camada de Sombreamento utilizando 2 fontes luminosas e outros ajustes, para evidenciar os detalhes sem sobrecarregar o aspecto visual.
- Alterar a visibilidade das camadas ou grupo de camadas usando niveis de zoom ao invés de escalas.
- Altere o nivel de zoom do canvas usando um seletor especifico.

## Versão mínima

- Versão mínima do QGis: 3.28 (LTR)

## Breve Tutorial

### Preparando o projeto

Você pode acessar o plugin clicando com o botão direito do mouse em qualquer local da barra de ícones e habilitando a opção **Webmap Plugin Toolbar**. Em seguida, clique no ícone ![](/images/configure_project.png) para configurar o seu projeto com as escalas normalmente utilizadas em webmaps. Você poderá mudar isso posteriormente indo em Project -> Properties -> View Settings -> Project Predefined e então colocando as escalas que preferir (ou simplesmente removendo as que estão lá para usar as escalas default do QGis). Lembre-se que, seja lá quais escalas você estive usando, a contagem de nives de zoom começa sempre em 0. Isto é, o nivel 0 é sempre a primeira escala definida na lista.

### ![](/images/cluster_view.png) Controlando a visibilidade utilizando clusters

Suponha que você tenha uma camada vetorial representando as cidades da América do Sul. Não seria interessante, claro, mostrar todas as cidades de uma só vez, em todas as escalas. O mapa ficaria confuso com tantos rótulos e ícons em sobreposição.

O algoritmo **Clustered Visualizarion** resolve isso agrupando cidades próximas (portanto criando clusters) e tornando visíveis apenas as cidades mais populosas de cada grupo, usando um atributo chamado **populacao** por exemplo. Essa clusterização das cidades é feita por distância: você pode definir, por exemplo, que cada cluster é formado por cidades cuja distância uma para outra seja de no máximo 20km. 

Conforme o usuário vai dando zoom, o algoritmo vai dividindo por 2 a distância inicial para formar novos clusters. Cidades que estavam previamente visíveis continuarão visíveis, mas novas cidades serão mostradas também... sempre com base no atributo **populacao**. Esse processo se repete por quantas vezes o usuário definir.

Para executar esse algoritmo, clique em ![](/images/cluster_view.png) e siga as isntrução descritas na tela que se abrirá (inclusive para entender as demais opções). O resultado é uma camada vetorial contendo os mesmo atributos originais da camada, mas adicionando um novo atributo chamado **_visibility_offset** (isso pode ser alterado também). Esse atributo precisa ser utilizado junto com a função **visibilityByOffset** (também provida pelo plugin) na opção **Data Defined Override** de alguma parte da Simbologia.

Por exemplo, se quisermos controlar a visibilidade dos rótulos teríamos que ir em Layer Properties -> Simbology -> Rendering -> Show Label -> Edit e usar a função **visibilityByOffset**. O primeiro parâmetro dessa função indica a partir de qual nivel de zoom a camada como um todo estará visivel (se você quer que a camada esteja visível apenas a partir do nivel 4, então esse primeiro argumento seria o número 4). O segundo argumento recebe basicamente o atributo criado pelo algoritmo, o **_visibility_offset**. Veja na imagem abaixo como ficaria:

![](/images/using_visibility_offset.png)


### ![](/images/grid_visualization.png) Controlando a visibilidade através de Grids

Outra forma de organizar a visibilidade das features de uma camada vetorial é através de uma visualização em grid. Funciona assim: o algoritmo cria um grid imaginário com pontos igualmente espaçados entre si e torna visível apenas a feature mais próxima de cada ponto do grid. A cada novo zoom, a distância entre os pontos do grid é reduzida pela metade e novas features, sempre as mais próximas de cada ponto, são tornadas visíveis.

Para executar esse algoritmo, clique em ![](/images/grid_visualization.png) e siga as instruções descritas lá. Os passos após a execução do algoritmo são os mesmos já descritos na seção anterior.

### ![](/images/aerial_perspective.png) Aplicando o efeito Perspectiva Aérea em uma camada de Sombreamento

Esse algoritmo aplica o efeito Perspectiva Aérea a uma camada de sombreamento. Esse efeito consiste em aumentar o constraste do sombreamento em regiões mais altas e diminuir em regiões mais baixas. O resultado é uma camada de Sombreamento mais suave, que tende a facilitar a composição dessa camada com rótulos e outros elementos do mapa.

Os dois principais parâmetros, Minimum Contrast e Maximum Contrast, controlam a intensidade do contraste: valores positivos aumentam o contraste, valores negative diminuem o contraste. Basicamente, quanto maior a diferença entre esse dois valores, maior o efeito da perspectiva aérea. Você deve testar diferentes valores para chegar no melhor desejado. Como recomendação geral, deve-se manter o contraste mínimo em valores negativos e o contraste máximo em números positivos não muito longe de 0. Teste os seguintes intervalos, por exemplo:

- Min: -100 Max: 0
- Min: -50 Max: 0
- Min: -20 Max: 20

Para usar essa ferramenta, clique em ![](/images/aerial_perspective.png) e siga as instruções descritas lá.

### ![](/images/relief_creator.png) Criando um Sombreamento usando 2 fontes de luz

Esse algoritmo combina duas camadas de Hillshade, criadas com duas fontes luminosas e diferentes configurações de brilho e contraste, para gerar um sombreamento mais detalhado e ainda assim mais agradável visualmente. O efeito Perspectiva Aérea é automaticamente aplicado.

Para executar esse algoritmo, clique em ![](/images/relief_creator.png) e siga as instruções descritas lá.

### Outras funcionalidades

- Seletor de niveis de zoom, para complementar o seletor de escalas padrão do Qgis.
- Clique com o botão direito do mouse em qualquer camada ou grupo de camadas e vá em **Set Layer Zoom Level Visibility** para configurar a visibilidade da camada usando niveis de zoom ao invés de escalas.
