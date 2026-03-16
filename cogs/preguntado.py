import discord
from discord.ext import commands
import random
import asyncio

COLOR = discord.Color.blurple()
COLOR_ERROR = discord.Color.red()
COLOR_WIN = discord.Color.green()

PREGUNTAS = {
    "Historia": [
        {"p":"¿En qué año comenzó la Primera Guerra Mundial?","ops":["1914","1918","1939","1905"],"r":"1914"},
        {"p":"¿Quién fue el primer presidente de Argentina?","ops":["Bernardino Rivadavia","José de San Martín","Manuel Belgrano","Julio Roca"],"r":"Bernardino Rivadavia"},
        {"p":"¿En qué año cayó el Muro de Berlín?","ops":["1989","1991","1985","1979"],"r":"1989"},
        {"p":"¿Qué civilización construyó las pirámides de Giza?","ops":["Egipcia","Griega","Romana","Mesopotámica"],"r":"Egipcia"},
        {"p":"¿En qué año llegó Cristóbal Colón a América?","ops":["1492","1498","1488","1502"],"r":"1492"},
        {"p":"¿Quién fue Napoleón Bonaparte?","ops":["Emperador francés","Rey inglés","Zar ruso","Kaiser alemán"],"r":"Emperador francés"},
        {"p":"¿En qué año terminó la Segunda Guerra Mundial?","ops":["1945","1943","1947","1941"],"r":"1945"},
        {"p":"¿Quién fue el líder de la Revolución Cubana?","ops":["Fidel Castro","Che Guevara","Batista","Raúl Castro"],"r":"Fidel Castro"},
        {"p":"¿En qué año se declaró la independencia de Argentina?","ops":["1816","1810","1820","1812"],"r":"1816"},
        {"p":"¿Qué país lanzó las primeras bombas atómicas?","ops":["Estados Unidos","Rusia","Alemania","Japón"],"r":"Estados Unidos"},
        {"p":"¿Quién fue el último faraón de Egipto?","ops":["Cleopatra","Ramsés II","Tutankamón","Nefertiti"],"r":"Cleopatra"},
        {"p":"¿En qué año se produjo la Revolución Francesa?","ops":["1789","1776","1804","1815"],"r":"1789"},
        {"p":"¿Quién conquistó el Imperio Azteca?","ops":["Hernán Cortés","Francisco Pizarro","Cristóbal Colón","Pedro de Alvarado"],"r":"Hernán Cortés"},
        {"p":"¿En qué año se fundó Roma?","ops":["753 a.C.","509 a.C.","476 a.C.","264 a.C."],"r":"753 a.C."},
        {"p":"¿Qué imperio fue el más grande de la historia?","ops":["Imperio Mongol","Imperio Romano","Imperio Británico","Imperio Español"],"r":"Imperio Mongol"},
        {"p":"¿Quién fue el primer hombre en llegar a la Luna?","ops":["Neil Armstrong","Buzz Aldrin","Yuri Gagarin","John Glenn"],"r":"Neil Armstrong"},
        {"p":"¿En qué año comenzó la Guerra de Malvinas?","ops":["1982","1978","1985","1976"],"r":"1982"},
        {"p":"¿Quién fue el primer presidente de Estados Unidos?","ops":["George Washington","Abraham Lincoln","Thomas Jefferson","Benjamin Franklin"],"r":"George Washington"},
        {"p":"¿En qué año cayó el Imperio Romano de Occidente?","ops":["476","410","395","380"],"r":"476"},
        {"p":"¿Qué guerra duró 100 años entre Francia e Inglaterra?","ops":["Guerra de los Cien Años","Guerra de las Rosas","Guerra de los Treinta Años","Guerra de Sucesión"],"r":"Guerra de los Cien Años"},
        {"p":"¿Quién lideró la independencia de Venezuela?","ops":["Simón Bolívar","José de San Martín","Francisco de Miranda","Antonio Sucre"],"r":"Simón Bolívar"},
        {"p":"¿En qué año se hundió el Titanic?","ops":["1912","1915","1908","1920"],"r":"1912"},
        {"p":"¿Qué civilización construyó Machu Picchu?","ops":["Inca","Azteca","Maya","Olmeca"],"r":"Inca"},
        {"p":"¿En qué año comenzó la Segunda Guerra Mundial?","ops":["1939","1941","1937","1935"],"r":"1939"},
        {"p":"¿Quién fue Alejandro Magno?","ops":["Rey de Macedonia","Emperador Romano","Faraón egipcio","Rey de Persia"],"r":"Rey de Macedonia"},
        {"p":"¿En qué año se produjo la Revolución Rusa?","ops":["1917","1905","1922","1914"],"r":"1917"},
        {"p":"¿Qué país inventó la guillotina?","ops":["Francia","Inglaterra","España","Italia"],"r":"Francia"},
        {"p":"¿Quién fue el primer secretario general de la ONU?","ops":["Trygve Lie","Dag Hammarskjöld","U Thant","Kurt Waldheim"],"r":"Trygve Lie"},
        {"p":"¿En qué año se firmó la Declaración de Independencia de EE.UU.?","ops":["1776","1783","1789","1775"],"r":"1776"},
        {"p":"¿Quién conquistó el Imperio Inca?","ops":["Francisco Pizarro","Hernán Cortés","Diego de Almagro","Pedro de Valdivia"],"r":"Francisco Pizarro"},
        {"p":"¿En qué año se produjo el ataque a Pearl Harbor?","ops":["1941","1942","1940","1943"],"r":"1941"},
        {"p":"¿Cuánto duró la Guerra Fría aproximadamente?","ops":["45 años","20 años","30 años","60 años"],"r":"45 años"},
        {"p":"¿Quién fue el dictador de España durante el siglo XX?","ops":["Francisco Franco","Miguel Primo de Rivera","José Antonio","Emilio Mola"],"r":"Francisco Franco"},
        {"p":"¿En qué año se creó la ONU?","ops":["1945","1919","1939","1950"],"r":"1945"},
        {"p":"¿Qué país fue el primero en dar el voto a la mujer?","ops":["Nueva Zelanda","Australia","Finlandia","Noruega"],"r":"Nueva Zelanda"},
    ],
    "Ciencia": [
        {"p":"¿Cuál es el símbolo químico del oro?","ops":["Au","Ag","Fe","Cu"],"r":"Au"},
        {"p":"¿Cuántos planetas tiene el sistema solar?","ops":["8","9","7","10"],"r":"8"},
        {"p":"¿Qué científico formuló la teoría de la relatividad?","ops":["Einstein","Newton","Hawking","Darwin"],"r":"Einstein"},
        {"p":"¿Cuál es el elemento más abundante en el universo?","ops":["Hidrógeno","Oxígeno","Helio","Carbono"],"r":"Hidrógeno"},
        {"p":"¿A qué velocidad viaja la luz?","ops":["300.000 km/s","150.000 km/s","500.000 km/s","100.000 km/s"],"r":"300.000 km/s"},
        {"p":"¿Qué planeta es el más grande del sistema solar?","ops":["Júpiter","Saturno","Urano","Neptuno"],"r":"Júpiter"},
        {"p":"¿Cuántos huesos tiene el cuerpo humano adulto?","ops":["206","198","215","220"],"r":"206"},
        {"p":"¿Cuál es la fórmula del agua?","ops":["H2O","CO2","NaCl","H2O2"],"r":"H2O"},
        {"p":"¿Qué científico describió la ley de la gravedad?","ops":["Newton","Einstein","Galileo","Kepler"],"r":"Newton"},
        {"p":"¿Qué órgano bombea la sangre?","ops":["Corazón","Pulmón","Hígado","Riñón"],"r":"Corazón"},
        {"p":"¿Cuántos cromosomas tiene una célula humana normal?","ops":["46","23","48","44"],"r":"46"},
        {"p":"¿Cuál es el planeta más cercano al Sol?","ops":["Mercurio","Venus","Tierra","Marte"],"r":"Mercurio"},
        {"p":"¿Qué es el ADN?","ops":["Ácido desoxirribonucleico","Aminoácido dinitrogénico","Ácido dinitroso","Adenosín difosfato"],"r":"Ácido desoxirribonucleico"},
        {"p":"¿Cuántos elementos tiene la tabla periódica actualmente?","ops":["118","108","92","115"],"r":"118"},
        {"p":"¿Qué tipo de energía produce una central nuclear?","ops":["Energía atómica","Energía solar","Energía eólica","Energía geotérmica"],"r":"Energía atómica"},
        {"p":"¿Cuál es el hueso más largo del cuerpo humano?","ops":["Fémur","Tibia","Húmero","Radio"],"r":"Fémur"},
        {"p":"¿Qué planeta tiene los anillos más visibles?","ops":["Saturno","Júpiter","Urano","Neptuno"],"r":"Saturno"},
        {"p":"¿Cuál es el símbolo químico del hierro?","ops":["Fe","Ir","Hi","Fr"],"r":"Fe"},
        {"p":"¿Qué gas es el más abundante en la atmósfera terrestre?","ops":["Nitrógeno","Oxígeno","Dióxido de carbono","Argón"],"r":"Nitrógeno"},
        {"p":"¿Cuántas galaxias tiene aproximadamente el universo observable?","ops":["2 billones","200 millones","500 mil millones","1 billón"],"r":"2 billones"},
        {"p":"¿Qué es la fotosíntesis?","ops":["Proceso de plantas que convierte luz en energía","Proceso de digestión animal","Proceso de respiración celular","División celular"],"r":"Proceso de plantas que convierte luz en energía"},
        {"p":"¿Cuál es el metal más conductor de electricidad?","ops":["Plata","Cobre","Oro","Aluminio"],"r":"Plata"},
        {"p":"¿Qué planeta rota al revés respecto a los demás?","ops":["Venus","Urano","Neptuno","Saturno"],"r":"Venus"},
        {"p":"¿Cuántas neuronas tiene el cerebro humano aproximadamente?","ops":["86 mil millones","1 billón","10 mil millones","500 millones"],"r":"86 mil millones"},
        {"p":"¿Qué es un agujero negro?","ops":["Región con gravedad tan intensa que ni la luz escapa","Estrella muerta","Planeta sin atmósfera","Nebulosa colapsada"],"r":"Región con gravedad tan intensa que ni la luz escapa"},
        {"p":"¿Cuál es el punto de ebullición del agua a nivel del mar?","ops":["100°C","90°C","110°C","95°C"],"r":"100°C"},
        {"p":"¿Qué vitamina produce el cuerpo con la luz solar?","ops":["Vitamina D","Vitamina C","Vitamina A","Vitamina B12"],"r":"Vitamina D"},
        {"p":"¿Cuál es el símbolo del sodio?","ops":["Na","So","Sd","Nm"],"r":"Na"},
        {"p":"¿Qué es la gravedad?","ops":["Fuerza de atracción entre masas","Fuerza electromagnética","Fuerza nuclear fuerte","Fuerza de repulsión"],"r":"Fuerza de atracción entre masas"},
        {"p":"¿Cuánto tarda la luz del Sol en llegar a la Tierra?","ops":["8 minutos","1 hora","24 horas","1 minuto"],"r":"8 minutos"},
        {"p":"¿Qué organismo descubrió la penicilina?","ops":["Alexander Fleming","Louis Pasteur","Marie Curie","Edward Jenner"],"r":"Alexander Fleming"},
        {"p":"¿Cuántas capas tiene la Tierra?","ops":["4","3","5","2"],"r":"4"},
        {"p":"¿Qué es la mitosis?","ops":["División celular que produce células idénticas","Fusión de células","Muerte celular programada","Reproducción sexual"],"r":"División celular que produce células idénticas"},
        {"p":"¿Cuál es el elemento más liviano?","ops":["Hidrógeno","Helio","Litio","Berilio"],"r":"Hidrógeno"},
        {"p":"¿Qué instrumento mide la temperatura?","ops":["Termómetro","Barómetro","Higrómetro","Anemómetro"],"r":"Termómetro"},
    ],
    "Deportes": [
        {"p":"¿Cuántos jugadores tiene un equipo de fútbol?","ops":["11","10","12","9"],"r":"11"},
        {"p":"¿En qué país se originó el fútbol moderno?","ops":["Inglaterra","Brasil","Francia","España"],"r":"Inglaterra"},
        {"p":"¿Qué país ganó el Mundial 2022?","ops":["Argentina","Francia","Brasil","Croacia"],"r":"Argentina"},
        {"p":"¿Cuántos aros tiene el símbolo olímpico?","ops":["5","4","6","3"],"r":"5"},
        {"p":"¿Qué deporte se practica en Wimbledon?","ops":["Tenis","Golf","Cricket","Rugby"],"r":"Tenis"},
        {"p":"¿Cuántos jugadores hay en un equipo de básquet?","ops":["5","6","4","7"],"r":"5"},
        {"p":"¿Qué país ha ganado más Copas del Mundo de fútbol?","ops":["Brasil","Argentina","Alemania","Italia"],"r":"Brasil"},
        {"p":"¿Cuánto dura un partido de fútbol?","ops":["90 minutos","80 minutos","100 minutos","75 minutos"],"r":"90 minutos"},
        {"p":"¿En qué deporte se usa un palo y pelota pequeña blanca?","ops":["Golf","Hockey","Cricket","Polo"],"r":"Golf"},
        {"p":"¿Cuántos Grand Slams ganó Roger Federer?","ops":["20","19","17","22"],"r":"20"},
        {"p":"¿En qué año se realizaron los primeros Juegos Olímpicos modernos?","ops":["1896","1900","1892","1904"],"r":"1896"},
        {"p":"¿Qué país organizó el Mundial 2018?","ops":["Rusia","Brasil","Alemania","Francia"],"r":"Rusia"},
        {"p":"¿Cuántos puntos vale un try en rugby?","ops":["5","3","4","6"],"r":"5"},
        {"p":"¿Qué club ganó más Champions League?","ops":["Real Madrid","Barcelona","Bayern Múnich","Milan"],"r":"Real Madrid"},
        {"p":"¿En qué deporte existe el término 'jaque mate'?","ops":["Ajedrez","Damas","Go","Backgammon"],"r":"Ajedrez"},
        {"p":"¿Cuántos sets tiene un partido de tenis al mejor de 5?","ops":["5","3","7","4"],"r":"5"},
        {"p":"¿Qué deporte practica LeBron James?","ops":["Básquet","Béisbol","Fútbol americano","Tenis"],"r":"Básquet"},
        {"p":"¿En qué país nació Lionel Messi?","ops":["Argentina","Uruguay","Brasil","España"],"r":"Argentina"},
        {"p":"¿Cuántos jugadores hay en un equipo de vóley?","ops":["6","5","7","8"],"r":"6"},
        {"p":"¿Qué deporte se juega en el Masters de Augusta?","ops":["Golf","Tenis","Polo","Cricket"],"r":"Golf"},
        {"p":"¿Cuántos metros mide una piscina olímpica?","ops":["50","25","100","75"],"r":"50"},
        {"p":"¿En qué año Argentina ganó su primer Mundial?","ops":["1978","1986","1990","1974"],"r":"1978"},
        {"p":"¿Quién es el máximo goleador histórico de la Selección Argentina?","ops":["Lionel Messi","Gabriel Batistuta","Hernán Crespo","Sergio Agüero"],"r":"Lionel Messi"},
        {"p":"¿Cuántos jugadores hay en un equipo de béisbol?","ops":["9","10","8","11"],"r":"9"},
        {"p":"¿Qué país tiene más medallas olímpicas en la historia?","ops":["Estados Unidos","Rusia","China","Alemania"],"r":"Estados Unidos"},
        {"p":"¿En qué deporte existe el 'home run'?","ops":["Béisbol","Cricket","Softball","Polo"],"r":"Béisbol"},
        {"p":"¿Cuánto mide una cancha de fútbol reglamentaria en largo?","ops":["105 metros","90 metros","120 metros","100 metros"],"r":"105 metros"},
        {"p":"¿Qué equipo ganó la Copa Libertadores 2023?","ops":["Fluminense","Boca Juniors","Flamengo","Olimpia"],"r":"Fluminense"},
        {"p":"¿En qué deporte compite Novak Djokovic?","ops":["Tenis","Squash","Bádminton","Ping pong"],"r":"Tenis"},
        {"p":"¿Cuántas disciplinas tiene el triatlón?","ops":["3","2","4","5"],"r":"3"},
        {"p":"¿Qué país organizó los Juegos Olímpicos de 2016?","ops":["Brasil","Argentina","Colombia","Chile"],"r":"Brasil"},
        {"p":"¿Cuántos rounds tiene un combate de boxeo profesional?","ops":["12","10","15","8"],"r":"12"},
        {"p":"¿En qué deporte se usa el término 'birdie'?","ops":["Golf","Tenis","Béisbol","Cricket"],"r":"Golf"},
        {"p":"¿Qué selección ganó la Eurocopa 2020?","ops":["Italia","Inglaterra","España","Francia"],"r":"Italia"},
        {"p":"¿Cuántos jugadores juegan al mismo tiempo en hockey sobre hielo?","ops":["6","5","7","4"],"r":"6"},
    ],
    "Geografía": [
        {"p":"¿Cuál es la capital de Australia?","ops":["Canberra","Sídney","Melbourne","Brisbane"],"r":"Canberra"},
        {"p":"¿Cuál es el río más largo del mundo?","ops":["Nilo","Amazonas","Yangtsé","Misisipi"],"r":"Nilo"},
        {"p":"¿Cuál es el país más grande del mundo?","ops":["Rusia","China","Canadá","Estados Unidos"],"r":"Rusia"},
        {"p":"¿Cuál es el océano más grande?","ops":["Pacífico","Atlántico","Índico","Ártico"],"r":"Pacífico"},
        {"p":"¿Cuál es la montaña más alta del mundo?","ops":["Everest","K2","Aconcagua","Kilimanjaro"],"r":"Everest"},
        {"p":"¿Cuál es la capital de Japón?","ops":["Tokio","Osaka","Kioto","Hiroshima"],"r":"Tokio"},
        {"p":"¿Qué país tiene más habitantes en el mundo?","ops":["India","China","Estados Unidos","Indonesia"],"r":"India"},
        {"p":"¿Cuál es el desierto más grande del mundo?","ops":["Sahara","Gobi","Atacama","Kalahari"],"r":"Sahara"},
        {"p":"¿Cuál es la capital de Argentina?","ops":["Buenos Aires","Córdoba","Rosario","Mendoza"],"r":"Buenos Aires"},
        {"p":"¿En qué continente está Brasil?","ops":["América del Sur","África","América Central","Asia"],"r":"América del Sur"},
        {"p":"¿Cuál es el país más pequeño del mundo?","ops":["Vaticano","Mónaco","San Marino","Liechtenstein"],"r":"Vaticano"},
        {"p":"¿Cuál es la capital de Francia?","ops":["París","Lyon","Marsella","Burdeos"],"r":"París"},
        {"p":"¿Por cuántos países pasa el río Amazonas?","ops":["9","5","3","12"],"r":"9"},
        {"p":"¿Cuál es el lago más grande del mundo?","ops":["Mar Caspio","Lago Superior","Lago Victoria","Lago Baikal"],"r":"Mar Caspio"},
        {"p":"¿En qué continente está Egipto?","ops":["África","Asia","Europa","Oriente Medio"],"r":"África"},
        {"p":"¿Cuál es la capital de Alemania?","ops":["Berlín","Múnich","Hamburgo","Frankfurt"],"r":"Berlín"},
        {"p":"¿Cuántos países tiene América del Sur?","ops":["12","10","14","11"],"r":"12"},
        {"p":"¿Cuál es el idioma más hablado del mundo?","ops":["Inglés","Mandarín","Español","Hindi"],"r":"Inglés"},
        {"p":"¿En qué país está la Torre Eiffel?","ops":["Francia","Bélgica","Italia","España"],"r":"Francia"},
        {"p":"¿Cuál es el punto más bajo de la Tierra?","ops":["Mar Muerto","Valle de la Muerte","Lago Assal","Fosa de las Marianas"],"r":"Mar Muerto"},
        {"p":"¿Cuántos países tiene África?","ops":["54","48","60","52"],"r":"54"},
        {"p":"¿Cuál es la capital de Brasil?","ops":["Brasilia","São Paulo","Río de Janeiro","Salvador"],"r":"Brasilia"},
        {"p":"¿Qué país tiene más fronteras terrestres?","ops":["China","Rusia","Brasil","Alemania"],"r":"China"},
        {"p":"¿En qué país está el río Nilo?","ops":["Egipto y Sudán","Solo Egipto","Etiopía y Egipto","Egipto y Libia"],"r":"Egipto y Sudán"},
        {"p":"¿Cuál es el volcán más alto del mundo?","ops":["Ojos del Salado","Mauna Kea","Kilimanjaro","Monte Etna"],"r":"Ojos del Salado"},
        {"p":"¿En qué continente está la Antártida?","ops":["Es su propio continente","América del Sur","Oceanía","No es un continente"],"r":"Es su propio continente"},
        {"p":"¿Cuál es la capital de Canadá?","ops":["Ottawa","Toronto","Vancouver","Montreal"],"r":"Ottawa"},
        {"p":"¿Qué país tiene más islas en el mundo?","ops":["Suecia","Noruega","Indonesia","Filipinas"],"r":"Suecia"},
        {"p":"¿En qué país está el Monte Aconcagua?","ops":["Argentina","Chile","Bolivia","Perú"],"r":"Argentina"},
        {"p":"¿Cuál es el río más largo de América del Sur?","ops":["Amazonas","Paraná","Orinoco","São Francisco"],"r":"Amazonas"},
        {"p":"¿En qué país está el desierto de Atacama?","ops":["Chile","Perú","Bolivia","Argentina"],"r":"Chile"},
        {"p":"¿Cuál es la capital de China?","ops":["Pekín","Shanghái","Hong Kong","Nankín"],"r":"Pekín"},
        {"p":"¿Qué océano separa Europa de América?","ops":["Atlántico","Pacífico","Índico","Ártico"],"r":"Atlántico"},
        {"p":"¿Cuántos países forman América Central?","ops":["7","5","8","6"],"r":"7"},
        {"p":"¿Cuál es la ciudad más poblada del mundo?","ops":["Tokio","Delhi","Shanghái","São Paulo"],"r":"Tokio"},
    ],
    "Entretenimiento": [
        {"p":"¿Quién creó a Mickey Mouse?","ops":["Walt Disney","Steven Spielberg","Jim Henson","Chuck Jones"],"r":"Walt Disney"},
        {"p":"¿En qué película aparece Simba?","ops":["El Rey León","Bambi","Dumbo","Tarzan"],"r":"El Rey León"},
        {"p":"¿Qué banda es conocida como 'Los Fab Four'?","ops":["The Beatles","Rolling Stones","Led Zeppelin","Queen"],"r":"The Beatles"},
        {"p":"¿En qué año se estrenó la primera película de Star Wars?","ops":["1977","1980","1975","1983"],"r":"1977"},
        {"p":"¿Qué personaje de Marvel tiene el escudo?","ops":["Capitán América","Iron Man","Thor","Hulk"],"r":"Capitán América"},
        {"p":"¿En qué serie aparece Walter White?","ops":["Breaking Bad","Better Call Saul","Narcos","Ozark"],"r":"Breaking Bad"},
        {"p":"¿Qué artista cantó 'Thriller'?","ops":["Michael Jackson","Prince","Madonna","David Bowie"],"r":"Michael Jackson"},
        {"p":"¿En qué país se produjo 'Squid Game'?","ops":["Corea del Sur","Japón","China","Tailandia"],"r":"Corea del Sur"},
        {"p":"¿Quién es el protagonista de Harry Potter?","ops":["Harry Potter","Ron Weasley","Hermione Granger","Dumbledore"],"r":"Harry Potter"},
        {"p":"¿En qué película aparece el personaje Jack Sparrow?","ops":["Piratas del Caribe","La Isla de la Fantasía","Tesoro Nacional","Náufrago"],"r":"Piratas del Caribe"},
        {"p":"¿Qué artista es conocida como 'La Reina del Pop'?","ops":["Madonna","Beyoncé","Lady Gaga","Britney Spears"],"r":"Madonna"},
        {"p":"¿En qué serie viven los Simpson?","ops":["Springfield","Shelbyville","Capital City","Ogdenville"],"r":"Springfield"},
        {"p":"¿Quién interpretó a Iron Man en el MCU?","ops":["Robert Downey Jr.","Chris Evans","Chris Hemsworth","Mark Ruffalo"],"r":"Robert Downey Jr."},
        {"p":"¿Qué película ganó el Oscar a Mejor Película en 2020?","ops":["Parásitos","1917","Joker","Había una vez en Hollywood"],"r":"Parásitos"},
        {"p":"¿De qué país es la serie 'La Casa de Papel'?","ops":["España","Argentina","México","Colombia"],"r":"España"},
        {"p":"¿Qué artista tiene el álbum más vendido de la historia?","ops":["Michael Jackson","The Beatles","Elvis Presley","Madonna"],"r":"Michael Jackson"},
        {"p":"¿En qué película aparece el personaje Voldemort?","ops":["Harry Potter","El Señor de los Anillos","Narnia","Crepúsculo"],"r":"Harry Potter"},
        {"p":"¿Quién canta 'Despacito'?","ops":["Luis Fonsi","J Balvin","Bad Bunny","Maluma"],"r":"Luis Fonsi"},
        {"p":"¿En qué año se estrenó 'El Señor de los Anillos: La Comunidad del Anillo'?","ops":["2001","1999","2003","2000"],"r":"2001"},
        {"p":"¿Qué personaje dice 'Hasta la vista, baby'?","ops":["Terminator","Rambo","Rocky","Die Hard"],"r":"Terminator"},
        {"p":"¿Cuántas temporadas tiene 'Game of Thrones'?","ops":["8","7","9","6"],"r":"8"},
        {"p":"¿Quién canta 'Shape of You'?","ops":["Ed Sheeran","Justin Bieber","Harry Styles","Sam Smith"],"r":"Ed Sheeran"},
        {"p":"¿En qué película aparece Forrest Gump?","ops":["Forrest Gump","Cast Away","Philadelphia","Big"],"r":"Forrest Gump"},
        {"p":"¿Qué superhéroe es Bruce Wayne?","ops":["Batman","Superman","Flash","Green Lantern"],"r":"Batman"},
        {"p":"¿De qué país es la banda BTS?","ops":["Corea del Sur","Japón","China","Tailandia"],"r":"Corea del Sur"},
        {"p":"¿Quién dirige la saga de películas de 'El Señor de los Anillos'?","ops":["Peter Jackson","Steven Spielberg","James Cameron","Christopher Nolan"],"r":"Peter Jackson"},
        {"p":"¿En qué año se estrenó 'Titanic' de James Cameron?","ops":["1997","1995","1999","2000"],"r":"1997"},
        {"p":"¿Qué artista argentina es conocida como 'La Sole'?","ops":["Soledad Pastorutti","Mercedes Sosa","Lali Espósito","Nicki Nicole"],"r":"Soledad Pastorutti"},
        {"p":"¿En qué ciudad vive Batman?","ops":["Ciudad Gótica","Metrópolis","Star City","Central City"],"r":"Ciudad Gótica"},
        {"p":"¿Qué canción de Queen fue usada en 'Bohemian Rhapsody'?","ops":["Bohemian Rhapsody","We Will Rock You","Don't Stop Me Now","Radio Ga Ga"],"r":"Bohemian Rhapsody"},
        {"p":"¿Quién es la creadora de la saga de libros de Harry Potter?","ops":["J.K. Rowling","Stephenie Meyer","Suzanne Collins","Veronica Roth"],"r":"J.K. Rowling"},
        {"p":"¿En qué serie trabaja el personaje Michael Scott?","ops":["The Office","Parks and Recreation","30 Rock","Arrested Development"],"r":"The Office"},
        {"p":"¿Cuántas películas tiene la saga principal de Star Wars?","ops":["9","6","12","8"],"r":"9"},
        {"p":"¿Qué artista cantó 'Bad Guy'?","ops":["Billie Eilish","Olivia Rodrigo","Dua Lipa","Ariana Grande"],"r":"Billie Eilish"},
        {"p":"¿En qué año se estrenó 'Avatar' de James Cameron?","ops":["2009","2007","2011","2005"],"r":"2009"},
    ],
    "Tecnología": [
        {"p":"¿Quién fundó Apple?","ops":["Steve Jobs","Bill Gates","Mark Zuckerberg","Elon Musk"],"r":"Steve Jobs"},
        {"p":"¿Qué significa 'CPU'?","ops":["Unidad Central de Proceso","Control de Puerto USB","Computadora Personal Única","Central de Procesamiento"],"r":"Unidad Central de Proceso"},
        {"p":"¿En qué año se fundó Google?","ops":["1998","1995","2000","2001"],"r":"1998"},
        {"p":"¿Qué lenguaje creó Guido van Rossum?","ops":["Python","Java","C++","Ruby"],"r":"Python"},
        {"p":"¿Qué significa 'RAM'?","ops":["Memoria de Acceso Aleatorio","Memoria de Alta Resolución","Red de Acceso Múltiple","Registro de Almacenamiento"],"r":"Memoria de Acceso Aleatorio"},
        {"p":"¿Qué empresa creó Windows?","ops":["Microsoft","Apple","Google","IBM"],"r":"Microsoft"},
        {"p":"¿Qué significa 'HTML'?","ops":["Lenguaje de Marcas de Hipertexto","Herramienta de Modificación de Texto","Hipertexto para Múltiples Tareas","Lenguaje de Modelado"],"r":"Lenguaje de Marcas de Hipertexto"},
        {"p":"¿Quién inventó el teléfono?","ops":["Alexander Graham Bell","Thomas Edison","Nikola Tesla","Marconi"],"r":"Alexander Graham Bell"},
        {"p":"¿Qué empresa desarrolló Android?","ops":["Google","Samsung","Apple","Microsoft"],"r":"Google"},
        {"p":"¿En qué año se lanzó el primer iPhone?","ops":["2007","2005","2009","2010"],"r":"2007"},
        {"p":"¿Qué significa 'URL'?","ops":["Localizador Uniforme de Recursos","Unidad de Red Local","Usuario Remoto de Linux","Lenguaje Universal de Recursos"],"r":"Localizador Uniforme de Recursos"},
        {"p":"¿Quién fundó Tesla?","ops":["Elon Musk","Martin Eberhard","Jeff Bezos","Larry Page"],"r":"Martin Eberhard"},
        {"p":"¿Qué empresa creó el procesador M1?","ops":["Apple","Intel","AMD","Qualcomm"],"r":"Apple"},
        {"p":"¿En qué año se fundó Facebook?","ops":["2004","2003","2006","2005"],"r":"2004"},
        {"p":"¿Qué significa 'SSD'?","ops":["Unidad de Estado Sólido","Sistema de Almacenamiento Secundario","Disco de Seguridad Sincronizado","Servidor de Datos Seguro"],"r":"Unidad de Estado Sólido"},
        {"p":"¿Quién inventó la World Wide Web?","ops":["Tim Berners-Lee","Bill Gates","Steve Jobs","Vint Cerf"],"r":"Tim Berners-Lee"},
        {"p":"¿Qué lenguaje de programación usa principalmente la web?","ops":["JavaScript","Python","Java","C#"],"r":"JavaScript"},
        {"p":"¿En qué año se fundó Amazon?","ops":["1994","1998","1996","2000"],"r":"1994"},
        {"p":"¿Qué es el 'phishing'?","ops":["Estafa para robar datos personales","Virus informático","Tipo de red WiFi","Programa espía"],"r":"Estafa para robar datos personales"},
        {"p":"¿Qué significa 'GPU'?","ops":["Unidad de Procesamiento Gráfico","Gestor de Procesos del Usuario","Generador de Pantalla Universal","Gestor de Puertos USB"],"r":"Unidad de Procesamiento Gráfico"},
        {"p":"¿Quién es el CEO de Tesla y SpaceX?","ops":["Elon Musk","Jeff Bezos","Larry Page","Mark Zuckerberg"],"r":"Elon Musk"},
        {"p":"¿Qué empresa creó PlayStation?","ops":["Sony","Nintendo","Microsoft","Sega"],"r":"Sony"},
        {"p":"¿En qué año se fundó Twitter?","ops":["2006","2004","2008","2005"],"r":"2006"},
        {"p":"¿Qué es el 'open source'?","ops":["Software con código fuente público","Software gratuito","Software sin publicidad","Software para Linux"],"r":"Software con código fuente público"},
        {"p":"¿Qué significa 'IP' en redes?","ops":["Protocolo de Internet","Identificador Personal","Interfaz de Programa","Índice de Prioridad"],"r":"Protocolo de Internet"},
        {"p":"¿Quién fundó Microsoft?","ops":["Bill Gates y Paul Allen","Bill Gates solo","Steve Ballmer","Paul Allen solo"],"r":"Bill Gates y Paul Allen"},
        {"p":"¿Qué es un algoritmo?","ops":["Secuencia de instrucciones para resolver un problema","Tipo de virus","Lenguaje de programación","Base de datos"],"r":"Secuencia de instrucciones para resolver un problema"},
        {"p":"¿En qué año se lanzó YouTube?","ops":["2005","2004","2006","2007"],"r":"2005"},
        {"p":"¿Qué empresa creó el sistema operativo iOS?","ops":["Apple","Google","Microsoft","Samsung"],"r":"Apple"},
        {"p":"¿Qué significa 'VPN'?","ops":["Red Privada Virtual","Video en Pantalla Nueva","Verificación de Puerto de Red","Velocidad de Procesamiento Neto"],"r":"Red Privada Virtual"},
        {"p":"¿Qué lenguaje se usa principalmente para inteligencia artificial?","ops":["Python","Java","C++","Ruby"],"r":"Python"},
        {"p":"¿En qué año se fundó Netflix?","ops":["1997","2000","1995","2002"],"r":"1997"},
        {"p":"¿Qué empresa creó el buscador Bing?","ops":["Microsoft","Yahoo","AOL","Apple"],"r":"Microsoft"},
        {"p":"¿Qué es el 'cloud computing'?","ops":["Computación en la nube usando servidores remotos","Computación con energía solar","Red inalámbrica avanzada","Almacenamiento en dispositivos USB"],"r":"Computación en la nube usando servidores remotos"},
        {"p":"¿Cuántos bits tiene un byte?","ops":["8","16","4","32"],"r":"8"},
    ],
    "Argentina": [
        {"p":"¿Cuál es la provincia más grande de Argentina?","ops":["Buenos Aires","Santa Cruz","Córdoba","Chubut"],"r":"Buenos Aires"},
        {"p":"¿En qué año fue el último golpe de estado en Argentina?","ops":["1976","1966","1955","1962"],"r":"1976"},
        {"p":"¿Cuál es el río más largo de Argentina?","ops":["Paraná","Uruguay","Colorado","Bermejo"],"r":"Paraná"},
        {"p":"¿Quién compuso el Himno Nacional Argentino?","ops":["Blas Parera","Vicente López y Planes","Manuel Belgrano","Mariano Moreno"],"r":"Blas Parera"},
        {"p":"¿Cuál es la montaña más alta de Argentina?","ops":["Aconcagua","Ojos del Salado","Monte Pissis","Mercedario"],"r":"Aconcagua"},
        {"p":"¿En qué ciudad nació el Che Guevara?","ops":["Rosario","Buenos Aires","Córdoba","Santa Fe"],"r":"Rosario"},
        {"p":"¿Cuál es la moneda actual de Argentina?","ops":["Peso argentino","Austral","Real","Peso uruguayo"],"r":"Peso argentino"},
        {"p":"¿Cuántas provincias tiene Argentina?","ops":["23","24","22","25"],"r":"23"},
        {"p":"¿Quién fue el primer presidente constitucional de Argentina?","ops":["Justo José de Urquiza","Bartolomé Mitre","Domingo Sarmiento","Bernardino Rivadavia"],"r":"Justo José de Urquiza"},
        {"p":"¿En qué provincia están las Cataratas del Iguazú?","ops":["Misiones","Corrientes","Entre Ríos","Formosa"],"r":"Misiones"},
        {"p":"¿Cuál es el animal nacional de Argentina?","ops":["Puma","Hornero","Cóndor","Yacaré"],"r":"Puma"},
        {"p":"¿En qué año Argentina volvió a la democracia?","ops":["1983","1985","1980","1987"],"r":"1983"},
        {"p":"¿Cuál es la flor nacional de Argentina?","ops":["Ceibo","Jacarandá","Lapacho","Orquídea"],"r":"Ceibo"},
        {"p":"¿En qué ciudad está el Teatro Colón?","ops":["Buenos Aires","Córdoba","Rosario","Mendoza"],"r":"Buenos Aires"},
        {"p":"¿Cuál es la segunda ciudad más poblada de Argentina?","ops":["Córdoba","Rosario","Mendoza","Tucumán"],"r":"Córdoba"},
        {"p":"¿En qué provincia está la Quebrada de Humahuaca?","ops":["Jujuy","Salta","Tucumán","Catamarca"],"r":"Jujuy"},
        {"p":"¿Quién escribió 'Martin Fierro'?","ops":["José Hernández","Jorge Luis Borges","Leopoldo Lugones","Ricardo Güiraldes"],"r":"José Hernández"},
        {"p":"¿Cuál es el lago más grande de Argentina?","ops":["Lago Nahuel Huapi","Lago Buenos Aires","Lago Argentino","Lago Viedma"],"r":"Lago Buenos Aires"},
        {"p":"¿En qué año fue el Mundial de Fútbol en Argentina?","ops":["1978","1982","1974","1986"],"r":"1978"},
        {"p":"¿Cuál es la danza nacional de Argentina?","ops":["Malambo","Tango","Zamba","Chacarera"],"r":"Malambo"},
        {"p":"¿Quién fue Jorge Luis Borges?","ops":["Escritor","Pintor","Músico","Político"],"r":"Escritor"},
        {"p":"¿En qué provincia está el Glaciar Perito Moreno?","ops":["Santa Cruz","Chubut","Neuquén","Río Negro"],"r":"Santa Cruz"},
        {"p":"¿Cuál es el pájaro nacional de Argentina?","ops":["Hornero","Cóndor","Pato sirirí","Cauquén"],"r":"Hornero"},
        {"p":"¿En qué año se adoptó la bandera argentina actual?","ops":["1818","1812","1816","1820"],"r":"1818"},
        {"p":"¿Cuál es la bebida más típica de Argentina?","ops":["Mate","Fernet","Vino","Terere"],"r":"Mate"},
        {"p":"¿En qué ciudad está la Casa Rosada?","ops":["Buenos Aires","La Plata","Córdoba","Rosario"],"r":"Buenos Aires"},
        {"p":"¿Quién fue el primer papa latinoamericano?","ops":["Francisco (Argentina)","Juan Pablo I","Benedicto XVI","Juan XXIII"],"r":"Francisco (Argentina)"},
        {"p":"¿Cuál es el deporte más popular de Argentina?","ops":["Fútbol","Básquet","Rugby","Tenis"],"r":"Fútbol"},
        {"p":"¿En qué provincia está la Península Valdés?","ops":["Chubut","Santa Cruz","Río Negro","Buenos Aires"],"r":"Chubut"},
        {"p":"¿Cuántos kilómetros de costa tiene Argentina aproximadamente?","ops":["4.725 km","3.000 km","6.000 km","2.500 km"],"r":"4.725 km"},
    ],
}


CATEGORIAS = list(PREGUNTAS.keys())
EMOJIS_CAT = {
    "Historia":       "📜",
    "Ciencia":        "🔬",
    "Deportes":       "⚽",
    "Geografía":      "🌍",
    "Entretenimiento":"🎬",
    "Tecnología":     "💻",
    "Argentina":      "🇦🇷",
}

partidas_pq = {}

# ─── CANAL TEMPORAL ───────────────────────────────────────
async def crear_canal_temporal_pq(guild, nombre, jugadores_members, categoria=None):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }
    for m in jugadores_members:
        overwrites[m] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)
    try:
        canal = await guild.create_text_channel(
            nombre,
            category=categoria,
            overwrites=overwrites,
            topic="Canal temporal de Preguntado ❓ — Se eliminará al terminar la partida."
        )
        return canal
    except discord.Forbidden:
        return None

async def eliminar_canal_temporal(canal, delay=15):
    await asyncio.sleep(delay)
    try:
        await canal.delete(reason="Partida de Preguntado finalizada")
    except:
        pass

# ─── PARTIDA ──────────────────────────────────────────────
class PartidaPreguntado:
    def __init__(self, canal_origen, num_preguntas, tiempo):
        self.canal_origen = canal_origen
        self.canal = None
        self.num_preguntas = num_preguntas
        self.tiempo = tiempo
        self.jugadores = {}
        self.respondieron = set()
        self.esperando_jugadores = True

    def get_ranking(self):
        return sorted(self.jugadores.items(), key=lambda x: x[1]["puntos"], reverse=True)

# ─── VISTA SALA ───────────────────────────────────────────
class VistaSalaPQ(discord.ui.View):
    def __init__(self, partida):
        super().__init__(timeout=300)
        self.partida = partida

    @discord.ui.button(label="✅ Unirse", style=discord.ButtonStyle.success)
    async def unirse(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid in self.partida.jugadores:
            await interaction.response.send_message("Ya estás en la partida.", ephemeral=True)
            return
        self.partida.jugadores[uid] = {"nombre": interaction.user.display_name, "puntos": 0, "member": interaction.user}
        nombres = ", ".join([v["nombre"] for v in self.partida.jugadores.values()])
        embed = interaction.message.embeds[0]
        embed.set_field_at(3, name=f"Jugadores ({len(self.partida.jugadores)})", value=nombres)
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("✅ ¡Te uniste!", ephemeral=True)

    @discord.ui.button(label="🚀 Iniciar", style=discord.ButtonStyle.primary)
    async def iniciar(self, interaction: discord.Interaction, button: discord.ui.Button):
        jugadores_ids = list(self.partida.jugadores.keys())
        if not jugadores_ids or interaction.user.id != jugadores_ids[0]:
            await interaction.response.send_message("Solo el creador puede iniciar.", ephemeral=True)
            return
        if len(self.partida.jugadores) < 1:
            await interaction.response.send_message("Necesitás al menos 1 jugador.", ephemeral=True)
            return
        self.stop()
        self.partida.esperando_jugadores = False
        await interaction.response.send_message("🚀 ¡Arrancamos!", ephemeral=True)
        await interaction.message.edit(view=None)
        await iniciar_preguntado(self.partida, interaction.message, interaction.guild)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        jugadores_ids = list(self.partida.jugadores.keys())
        if not jugadores_ids or interaction.user.id != jugadores_ids[0]:
            await interaction.response.send_message("Solo el creador puede cancelar.", ephemeral=True)
            return
        self.stop()
        partidas_pq.pop(self.partida.canal_origen.id, None)
        await interaction.message.edit(content="❌ Sala cancelada.", embed=None, view=None)
        await interaction.response.send_message("Cancelado.", ephemeral=True)

# ─── VISTA RESPUESTA ──────────────────────────────────────
class VistaRespuestaPQ(discord.ui.View):
    def __init__(self, partida, pregunta, opciones_mezcladas):
        super().__init__(timeout=partida.tiempo)
        self.partida = partida
        self.pregunta = pregunta
        self.opciones = opciones_mezcladas
        self._terminado = False

        for i, opcion in enumerate(opciones_mezcladas):
            btn = discord.ui.Button(
                label=f"{['A','B','C','D'][i]}) {opcion}",
                style=discord.ButtonStyle.primary,
                custom_id=f"op_{i}",
                row=0
            )
            btn.callback = self._responder(i, opcion)
            self.add_item(btn)

    def _responder(self, idx, opcion):
        async def callback(interaction: discord.Interaction):
            uid = interaction.user.id
            if uid not in self.partida.jugadores:
                await interaction.response.send_message("No estás en esta partida.", ephemeral=True)
                return
            if uid in self.partida.respondieron:
                await interaction.response.send_message("Ya respondiste.", ephemeral=True)
                return
            self.partida.respondieron.add(uid)
            es_correcta = opcion == self.pregunta["r"]
            if es_correcta:
                self.partida.jugadores[uid]["puntos"] += 1
                await interaction.response.send_message("✅ ¡Correcto!", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Incorrecto. Era **{self.pregunta['r']}**.", ephemeral=True)
            if len(self.partida.respondieron) == len(self.partida.jugadores) and not self._terminado:
                self._terminado = True
                self.stop()
        return callback

    async def on_timeout(self):
        if not self._terminado:
            self._terminado = True
            self.stop()

# ─── LÓGICA ───────────────────────────────────────────────
async def iniciar_preguntado(partida, mensaje_sala, guild):
    members = [v["member"] for v in partida.jugadores.values()]
    nombre_canal = f"preguntado-{partida.canal_origen.name[:15]}"
    categoria = partida.canal_origen.category

    canal_temp = await crear_canal_temporal_pq(guild, nombre_canal, members, categoria)
    if canal_temp:
        partida.canal = canal_temp
        embed_info = discord.Embed(
            title="❓ ¡Preguntado iniciado!",
            description=f"La partida se movió a {canal_temp.mention}\n¡Entren ahí para jugar!",
            color=COLOR
        )
        await mensaje_sala.edit(embed=embed_info)
    else:
        partida.canal = partida.canal_origen
        embed_info = discord.Embed(
            title="❓ ¡Preguntado iniciado!",
            description="⚠️ No pude crear canal temporal (falta permiso `Gestionar canales`). Jugando acá.",
            color=COLOR
        )
        await mensaje_sala.edit(embed=embed_info)

    pool = []
    for cat in CATEGORIAS:
        pool.extend([(p, cat) for p in PREGUNTAS[cat]])
    random.shuffle(pool)
    preguntas = pool[:partida.num_preguntas]

    for i, (pregunta, categoria_nombre) in enumerate(preguntas):
        if partida.canal_origen.id not in partidas_pq:
            return

        partida.respondieron = set()
        opciones = pregunta["ops"][:]
        random.shuffle(opciones)

        embed = discord.Embed(
            title=f"{EMOJIS_CAT[categoria_nombre]} Pregunta {i+1}/{partida.num_preguntas} — {categoria_nombre}",
            description=f"**{pregunta['p']}**",
            color=COLOR
        )
        for j, op in enumerate(opciones):
            embed.add_field(name=f"{['A','B','C','D'][j]}) {op}", value="\u200b", inline=True)
        embed.set_footer(text=f"⏱️ {partida.tiempo} segundos para responder")

        vista = VistaRespuestaPQ(partida, pregunta, opciones)
        msg = await partida.canal.send(embed=embed, view=vista)
        await vista.wait()

        correcta = pregunta["r"]
        no_resp = [v["nombre"] for uid, v in partida.jugadores.items() if uid not in partida.respondieron]

        embed_res = discord.Embed(title=f"✅ Respuesta: **{correcta}**", color=COLOR_WIN)
        ranking = partida.get_ranking()
        marcador = "\n".join([f"**{v['nombre']}**: {v['puntos']} pts" for _, v in ranking])
        embed_res.add_field(name="📊 Marcador", value=marcador, inline=False)
        if no_resp:
            embed_res.add_field(name="⏱️ No respondieron", value=", ".join(no_resp), inline=False)

        await msg.edit(view=None)
        await partida.canal.send(embed=embed_res)

        if i < partida.num_preguntas - 1:
            await asyncio.sleep(3)

    await mostrar_resultado_final(partida)

async def mostrar_resultado_final(partida):
    ranking = partida.get_ranking()
    embed = discord.Embed(title="🏆 ¡Fin del Preguntado!", color=COLOR_WIN)
    medallas = ["🥇","🥈","🥉"]
    desc = ""
    for i, (uid, v) in enumerate(ranking):
        m = medallas[i] if i < 3 else f"#{i+1}"
        desc += f"{m} **{v['nombre']}** — {v['puntos']}/{partida.num_preguntas} puntos\n"
    embed.description = desc
    embed.set_footer(text="¡Este canal se eliminará en 15 segundos!")
    await partida.canal.send(embed=embed)
    partidas_pq.pop(partida.canal_origen.id, None)
    if partida.canal != partida.canal_origen:
        asyncio.create_task(eliminar_canal_temporal(partida.canal, delay=15))

# ─── COG ──────────────────────────────────────────────────
class Preguntado(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.group(name="preguntado", aliases=["pq"], invoke_without_command=True)
    async def preguntado(self, ctx):
        embed = discord.Embed(title="❓ Preguntado — Ayuda", color=COLOR)
        embed.add_field(name="$preguntado crear [preguntas] [segundos]", value="Ejemplos:\n`$pq crear 10 30`\n`$pq crear 5 15`", inline=False)
        embed.add_field(name="Preguntas", value="Entre 5 y 20", inline=True)
        embed.add_field(name="Tiempo", value="Entre 10 y 60 segundos", inline=True)
        embed.add_field(name="📚 Categorías", value="Historia, Ciencia, Deportes, Geografía, Entretenimiento, Tecnología, 🇦🇷 Argentina", inline=False)
        embed.add_field(name="📌 Canal temporal", value="Al iniciar, se crea un canal privado para los jugadores", inline=False)
        await ctx.send(embed=embed)

    @preguntado.command(name="crear")
    async def crear(self, ctx, num_preguntas: int = 10, tiempo: int = 30):
        if ctx.channel.id in partidas_pq:
            await ctx.send(embed=discord.Embed(description="❌ Ya hay una partida en este canal.", color=COLOR_ERROR))
            return
        if not (5 <= num_preguntas <= 20):
            await ctx.send(embed=discord.Embed(description="❌ El número de preguntas debe estar entre 5 y 20.", color=COLOR_ERROR))
            return
        if not (10 <= tiempo <= 60):
            await ctx.send(embed=discord.Embed(description="❌ El tiempo debe estar entre 10 y 60 segundos.", color=COLOR_ERROR))
            return

        partida = PartidaPreguntado(ctx.channel, num_preguntas, tiempo)
        partida.jugadores[ctx.author.id] = {"nombre": ctx.author.display_name, "puntos": 0, "member": ctx.author}
        partidas_pq[ctx.channel.id] = partida

        embed = discord.Embed(title="❓ Sala de Preguntado", color=COLOR)
        embed.add_field(name="🔢 Preguntas", value=str(num_preguntas), inline=True)
        embed.add_field(name="⏱️ Tiempo por pregunta", value=f"{tiempo}s", inline=True)
        embed.add_field(name="📚 Categorías", value="Historia · Ciencia · Deportes · Geografía · Entretenimiento · Tecnología · 🇦🇷 Argentina", inline=True)
        embed.add_field(name="Jugadores (1)", value=ctx.author.display_name, inline=False)
        embed.set_footer(text="El creador inicia cuando estén todos | Se creará un canal privado al iniciar")
        await ctx.send(embed=embed, view=VistaSalaPQ(partida))

    @preguntado.command(name="terminar")
    @commands.has_permissions(administrator=True)
    async def terminar(self, ctx):
        if ctx.channel.id not in partidas_pq:
            await ctx.send(embed=discord.Embed(description="❌ No hay partida activa.", color=COLOR_ERROR))
            return
        partida = partidas_pq.pop(ctx.channel.id)
        await ctx.send(embed=discord.Embed(description="✅ Partida terminada.", color=COLOR))
        if partida.canal and partida.canal != partida.canal_origen:
            asyncio.create_task(eliminar_canal_temporal(partida.canal, delay=5))

    @crear.error
    async def crear_error(self, ctx, error):
        await ctx.send(embed=discord.Embed(description="❌ Uso: `$preguntado crear [5-20] [10-60]`", color=COLOR_ERROR))

async def setup(bot):
    await bot.add_cog(Preguntado(bot))