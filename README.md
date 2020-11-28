# datakyt
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-2-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

DataKyt is a system for equipment accounting.

## Installation

### How to expand PostgreSQL for Linux

- `sudo apt install postgresql-12`
- `export PGHOST=localhost`
- `sudo -u postgres psql`
- `postgres=# ALTER USER postgres PASSWORD '12345';`
- `psql -U postgres -d postgres -a -f create_database.sql`

## Usage

- TBD

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.


## Project status

In progress

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/aartiukh"><img src="https://avatars2.githubusercontent.com/u/6399458?v=4" width="100px;" alt=""/><br /><sub><b>Anton Artiukh</b></sub></a><br /><a href="#infra-aartiukh" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#talk-aartiukh" title="Talks">📢</a> <a href="https://github.com/MykytaKyt/datakyt/pulls?q=is%3Apr+reviewed-by%3Aaartiukh" title="Reviewed Pull Requests">👀</a></td>
    <td align="center"><a href="https://github.com/MykytaKyt"><img src="https://avatars1.githubusercontent.com/u/59031709?v=4" width="100px;" alt=""/><br /><sub><b>Mykyta Kyt</b></sub></a><br /><a href="#talk-MykytaKyt" title="Talks">📢</a> <a href="#example-MykytaKyt" title="Examples">💡</a> <a href="#design-MykytaKyt" title="Design">🎨</a> <a href="https://github.com/MykytaKyt/datakyt/commits?author=MykytaKyt" title="Documentation">📖</a> <a href="https://github.com/MykytaKyt/datakyt/commits?author=MykytaKyt" title="Code">💻</a></td>
  </tr>
</table>

<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
