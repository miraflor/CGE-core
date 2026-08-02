# Governance

CGE-Core is a small, single-maintainer open-source project.

## Roles

**Maintainer** — James Matthew Miraflor ([@miraflor](https://github.com/miraflor)).
The maintainer sets project direction, reviews and merges pull requests,
cuts releases, and is the contact for conduct reports.

**Contributors** — anyone who opens an issue or pull request. All
substantive contributions are credited in the changelog.

## Decision making

Decisions are made in public, in GitHub issues and pull requests.
Technical disagreements are resolved by discussion anchored to the
project's two fidelity commitments:

1. **Hosoe fidelity.** The bundled models must remain verifiable,
   equation by equation, against the GAMS Model Library references
   (`splcge.gms` SEQ=275, `stdcge.gms` SEQ=276) and Hosoe, Gasawa &
   Hashimoto (2010).
2. **Test-guarded behavior.** No change to numerical results without a
   changelog entry and a regression test; the CI solver job must pass
   with nothing skipped.

Where discussion does not converge, the maintainer decides.

## Changing this document

By pull request, merged by the maintainer. If the project grows
additional maintainers, this document will be revised to describe how
they are added and how responsibilities are shared.
