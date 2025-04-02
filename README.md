<p align="center">
<img src="https://raw.githubusercontent.com/AleksandrUsolcev/exams/main/readme_logo.png" width="360">
</p>

<br>

<p align="center">
<img src="https://img.shields.io/badge/Python-3.10%20|%203.11-brightgreen" alt="python version"> 
<img src="https://img.shields.io/badge/Django-3.2-orange" alt="django version">
<img src="https://img.shields.io/badge/PostgreSQL-15.1-blue" alt="postgresql version">
</p>

---

**Exams** — сервис для проведения тестирований, включающий в себя рейтинговую систему пользователей и возможность группирования тестов по спринтам.

Основной идеей проекта является создать легко-развертываемый инструментарий для проведения внутрикорпоративных тестирований, минуя сторонние общедоступные сервисы. Так же с текущим имеющимся функционалом проект может послужить вариантом для проведения тестирований в образовательной сфере.

## Технологии

- [Python](https://www.python.org/) >= 3.10
- [Django](https://github.com/django/django) 3.2
- [PostgreSQL](https://www.postgresql.org/) 15.1
- [Bootstrap](https://github.com/twbs/bootstrap) 5
- [Django Debug Toolbar](https://github.com/jazzband/django-debug-toolbar) 3.8.1
- [Django Nested Admin](https://github.com/theatlantic/django-nested-admin) 4.0.2
- [Django Admin Inteface](https://github.com/fabiocaccamo/django-admin-interface) 0.24.2
- [Django CKEditor](https://github.com/django-ckeditor/django-ckeditor) 6.5.1
- [Psycopg2 (binary)](https://github.com/psycopg/psycopg2) 2.9.5

## Запуск проекта в docker контейнере

Клонировать репозиторий, перейти в `exams/docker/` и копировать [образец](/docker/example.env) файла переменного окружения

```bash
git clone https://github.com/AleksandrUsolcev/exams.git
cd exams/docker/
cp example.env .env
``` 

Если проект не предполагается запускать в ознакомительных целях, рекомендуется отредактировать файл переменного окружения, в ином случае **следующий шаг можно пропустить**

```bash
nano .env
``` 
- **DB_ENGINE** - оставить без изменений
- **DB_HOST** - оставить без изменений
- **DB_NAME** - имя базы данных
- **POSTGRES_USER** - имя пользователя базы данных
- **POSTGRES_PASSWORD** - пароль для базы данных
- **DJANGO_SECRET_KEY** - придумать или [сгенерировать](https://djecrety.ir/) секретный ключ
- **ALLOWED_HOSTS** - оставить без изменений, если нет необходимости редактировать [docker-compose](/docker/docker-compose.yaml)

Развернуть docker контейнер

```bash
docker-compose up -d --build
``` 

После того как сайт будет доступен на `http://localhost/` создать суперпользователя

```bash
docker-compose exec web python manage.py createsuperuser
```

Перейти в админ-панель `http://localhost/admin/` под учетными данными суперпользователя и начать работу 

## Структура и описание проекта

Проект состоит из трех основных компонентов: [тестирования](#тестирования), [прогресс](#прогресс) и [пользователи](#пользователи). Ниже мы разберем их отдельно. Для лучшего и наглядного понимания желательно иметь уже [развернутый](#запуск-проекта-в-docker-контейнере) проект.

### Тестирования

Прежде чем перейти непосредственно к созданию первого теста необходимо добавить **категорию** и краткое описание к ней. По умолчанию категории сортируются по количеству относящихся к ним тестов, однако есть возможность вручную указать приоритет. Так же можно скрывать категории не имеющие тестов.

Опционально можно добавить **спринты**, в которые могут входить несколько тестов из разных категорий. Спринт будет считаться завершенным при успешном прохождении всех входящих в него тестирований. При этом можно настроить решение тестов внутри спринта как в случайном, так и в последовательном порядке.

После создания категории можно переходить к созданию и наполнению своего первого **теста**. Все настройки теста, добавление вопросов и вариантов ответа производятся на одной странице. Минуя очевидные параметры вроде названия, описания и категории стоит остановиться подробнее на детальных настройках теста:

- **Время на выполнение**: необязательный параметр указывает время для выполнения теста (в минутах) и отображает пользователю таймер в процессе прохождения. Если пользователь не успеет выполнить тест за указанное время, то результат не будет засчитан.
- **Процент верных ответов для прохождения**: необязательный параметр, который задает процент верных ответов для успешного завершения теста. Может применяться в паре с параметром **время на выполнение**.
- **Разрешить повторное прохождение**: параметр говорящий сам за себя. Если активен, тест можно проходить неограниченное количество раз, при этом прогресс каждого прохождения будет сохранен (о прогрессе будет дальше).
- **Отображать пользователю результат после каждого ответа и по окончанию тестирования**: если параметр активен, то после каждого данного ответа пользователь будет виден зачтен его ответ или нет. Так же после прохождения теста при выводе результатов, будут выводится все его ответы в процессе прохождения теста. Если же параметр активен, то пользователь до окончания тестирования так и не узнает успешность его прохождения, а так же в результатах будет выводиться лишь количество и процент его верных ответов.
- **Доступ для гостей к результатам только по ссылке-приглашению**: данный параметр имеет силу только если активен параметр выше (отображение результата). Если параметр активен, то гости смогут посмотреть результаты другого пользователя **только после получения от него ссылки-приглашения**, которая будет доступна пользователю после прохождения тестирования при просмотре им результатов. В ином случае, если параметр неактивен, то все гости смогут видеть подброные результаты пользователя.
- **Отображать пользователю верные варианты ответов**: в случае если параметр активен, то в результатах при неверно выбранных вариантах, будут подсвечиваться желтым верные ответы.
- **Перемешивать варианты ответов, игнорируя приоритет**: по умолчанию варианты ответов можно сортировать по их id или параметру приоритета, однако если данный параметр будет активен, то каждый раз варианты в вопросе будут перемешиваться в случайном порядке.
- **Разрешить оставлять выбор пустым**: параметр работает только с типами вопросов, где есть возможность указать несколько вариантов ответа. 
- **Приоритет**: необязательный параметр, влияющий на порядок выдачи теста, если он относится к спринту. По умолчанию в спринтах выдача тестов идет в порядке их создания.
- **Опубликован**: публикует тест, делая его видимым и доступным всем для прохождения. Зависим от параметра **Готов к публикации**.
- **Готов к публикации**: неизменяемый пользователем параметр, который служит заместо стандартной валидации. Так как данный параметр присутствует еще и в **вопросах**, подробнее разберем его [отдельно](#подробнее-о-параметре-готовности-к-публикации).

После заполнения вышеуказанных параметров **теста** на той же странице, ниже нам будет доступно добавление **вопросов**. Ниже подробнее разберем параметры **вопросов**:

- **Подробное описание/информация**: необязательное поле, в котором можно добавить большой объем информации к вопросу (например какая-либо теория с изображениями) и отформатировать его в текстовом редакторе на свое усмотрение.
- **Вопрос**: сам вопрос, за которым пользователю уже будет предоставлен выбор из вариантов ответов. Желательно небольшой по объему текст, которым можно подытожить подробную информацию, представленную в поле упомянутом ранее (если она есть).
- **Собщение после ответа**: необязательное поле, в котором можно указать текст выводимый пользователю, который он увидит после данного им ответа, при условии, если в **тесте** активен параметр **Отображать пользователю результат после каждого ответа и по окончанию тестирования**.
- **Приоритет**: необязательный параметр, влияющий на порядок выдачи вопроса в тесте. По умолчанию в тестах выдача вопросов идет в порядке их создания, при условии если они **активны** и **опубликованы**.
- **Тип**: выбор из трех типов, которые будут применяться для **ответов** - допустим только один правильный ответ, несколько правильных ответов, либо же пользователю необходимо будет ввести в текстовое поле ответ самому.
- **Опубликован**: публикует вопрос, делая его видимым и доступным в тесте. Зависим от параметра **Готов к публикации**.
- **Готов к публикации**: неизменяемый пользователем параметр, который служит заместо стандартной валидации. Подробнее о нем [отдельно](#подробнее-о-параметре-готовности-к-публикации).

После заполнения всех необходимых полей и параметров **вопроса** переходим к добавлению вариантов **ответов** ниже - заполняем крактий текст варианта, приоритет (по необходимости) и является ли данный вариант ответа верным. Собственно тут и стоит подробнее перейти к ранее упомянутому параметру **Готов к публикации** (active).

### Подробнее о параметре готовности к публикации

Так как при создании теста, добавлении вопросов и вариантов ответов к ним, возможна работа с потенциально большими объемами текста, то возникает потребность в частом сохранении теста. Стандартная валидация может мешать сохранению, если например в каких-либо вопросах пока еще отсутствуют готовые варианты ответов, подходящие под тип тестов. Поэтому если какой-либо вопрос **не удовлетворяет подходящим требованиям для публикации** (о них ниже), то при сохранении он просто будет **неактивен**. При **неактивном** статусе **готовности к публикации** не имеет значения статус параметра **публикации** как в случае с тестами, так в случае и с ответами.

Для того чтобы **тест** принял положительный статус **готовности к публикации** он должен включать в себя хотя бы один готовый к публикации и опубликованный **вопрос**.

Статус **готовности к публикации** вопросов уже зависит от их **типа** ответов:
- **Допустим один правильный ответ**: статус **готовности** будет положительным, если из представленных вариантов **только один** будет с указанным параметром как **верный**.
- **Допустимы несколько вариантов ответов**: статус **готовности** будет положительным, если из представленных вариантов **как минимум один** будет с указанным параметром как **верный**.
- **Текстовый ответ**: статус **готовности** будет положительным при условии наличия минимум одного ответа со статусом **верный**, однако стоит учитывать, что таких вариантов для этого типа можно указать несколько. Неверные варианты же можно использовать в качестве черновика - такие варианты не будут учитываться при валидации ответа пользователем.

### Прогресс

Прогресс пользователей делиться на прогресс прохождения **спринтов** или **тестов**. 

При прохождении спринтов фиксируется лишь дата начала прохождения и окончания. Посмотреть доступные для прохождения спринты и их статус, можно в соответствующем пункте на главной странице.

При прохождении пользователями тестов фиксируются дата начала и окончания прохождения теста, статус прохождения (зачтен или не зачтен), количество данных ответов и информация о стадии, на которой сейчас находится пользователь.

Ознакомиться с прогрессом всех пользователей можно перейдя на одноименный пункт меню на главной странице. Так же можно посмотреть прогресс по каждому тестированию отдельно, после его прохождения, либо в профиле интересующего Вас пользователя.

Стоит учитывать, что при каждом **повторном прохождении теста** (если такая возможность активна в настройках) процент в **рейтинге** засчитывается **за все** прохождения одного теста, дабы стимулировать пользователей успешно проходить тесты с наибольшим процентом верных вариантов и наименьшим количеством попыток.

В целях удобства в админ-панели имеется возможность сброса сразу всего связанного прогресса спринтов или тестов.

При успешном прохождении теста пользователю начисляются **баллы** в зависимости от количества данных ему верных ответов.

**Позиция в рейтинге** расчитывается исходя из следующего приоритета: **количество баллов** > **общий процент верных ответов** > **количество успешно пройденных тестов**

### Пользователи

Так как проект позиционируется в первую очередь для использования во внутрикорпоративной сети, то система аутентификации реализованна стандартными средствами. Для успешной работы системы сброса и смены пароля, необходимо отдельно [настраивать](https://docs.djangoproject.com/en/3.2/topics/email/) отправку почты в соответствии с собственными нуждами. Возможно данный нюанс, как и расширения аутентификации до двухфакторной появятся в [планах по доработке](#планы-по-доработке), но пока на текущем этапе развития проекта такой необходимости нет.

Зарегистрированный пользователь может отредактировать свой профиль - заполнить имя и фамилию, небольшую информацию о себе, а так же **скрыть** для отображения пройденные тесты и спринты.

Так же в профиле можно посмотреть информацию о количестве пройденных тестов, сколько из них зачтено, проценте верных ответов, баллов и месте в общем рейтинге.

## Автор

[Александр Усольцев](https://github.com/AleksandrUsolcev)
