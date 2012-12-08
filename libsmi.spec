# mib repository
%define mibsdir		%{_datadir}/%{name}/mibs
# pib repository
%define	pibsdir		%{_datadir}/%{name}/pibs

%define	major 2
%define libname %mklibname smi %{major}
%define develname %mklibname smi -d

Summary:	LibSMI deals with SNMP MIBS definitions
Name:		libsmi
Version:	0.4.8
Release:	9
License:	BSD-like
Group:		System/Libraries
URL:		http://www.ibr.cs.tu-bs.de/projects/libsmi/
Source0:	ftp://ftp.ibr.cs.tu-bs.de/pub/local/libsmi/%{name}-%{version}.tar.gz
Patch0:		libsmi-0.4.8-format_not_a_string_literal_and_no_format_arguments.diff
Patch1:		libsmi-0.4.8-CVE-2010-2891.diff
Requires:	coreutils
BuildRequires:	bison
BuildRequires:	flex
BuildRequires:  autoconf automake libtool
BuildRequires:	wget

%description
This package contains the SMI library and standard IETF and IANA Mibs. This
library provides a programmer-friendly interface to access MIB module
information.

System config file: %{_sysconfdir}/smi.conf
User config file:   .smirc

%package -n	%{libname}
Summary:	LibSMI deals with SNMP MIBS definitions
Group:          System/Libraries
Provides:	libsmi = %{version}-%{release}
Requires:	%{name}-mibs-std
Conflicts:	smi-tools < 0.4.5-1

%description -n	%{libname}
This package contains the shared SMI libraries and standard IETF and IANA Mibs.
This library provides a programmer-friendly interface to access MIB module
information.

System config file: %{_sysconfdir}/smi.conf
User config file:   .smirc

%package -n	%{develname}
Summary:	Development tools for LibSMI
Group:		Development/Other
Requires:	%{libname} >= %{version}-%{release}
Provides:	smi-devel = %{version}-%{release}
Provides:	libsmi-devel = %{version}-%{release}
Obsoletes:	%{mklibname smi 2 -d}

%description -n	%{develname}
This package contails the include files and static library needed to develop
applications based on the SMI Library

%package	mibs-std
Summary:	Standard MIB files for LibSMI
Group:		System/Libraries
Requires:	smi-tools >= %{version}-%{release}

%description	mibs-std
This package contains standard MIB files for use with the SMI Library:

 o IETF - standard MIBS for SNMP, SNMPv2, interfaces, IP, 
 o IANA - standard identifiers for protocols, ifType, etc.

%package	mibs-ext
Summary:	Extended MIB files for LibSMI
Group:		System/Libraries
Requires:	smi-tools = %{version}

%description	mibs-ext
This package contains Extended MIB files for use with the SMI Library:

 o IRTF - SMIng oids, extensions, types 
 o TUBS - MIBS for the Technical University of Braunschweig

%package -n	smi-tools
Summary:	LibSMI tools
Group:          Networking/Other
Requires:	%{libname} = %{version}
Requires:	wget

%description -n	smi-tools
This package contains the LibSMI tools.

%prep

%setup -q -n %{name}-%{version}
%patch0 -p0 -b .format_not_a_string_literal_and_no_format_arguments
%patch1 -p0 -b .CVE-2010-2891

%build

%configure2_5x \
    --with-mibdir=%{mibsdir} \
    --with-pibdir=%{pibsdir} \
    --with-smipath=%{mibsdir}/site:%{mibsdir}/ietf:%{mibsdir}/iana \
    --enable-smi \
    --enable-sming

%make

%check
# fails a couple of tests (2 in {0.4.4, 0.4.5})
make check ||:

%install
rm -rf %{buildroot}

%makeinstall_std

# something broke here...
rm -f %{buildroot}%{pibsdir}/*PIB*
rm -f %{buildroot}%{pibsdir}/*SPPI*
install -m0644 pibs/ietf/* %{buildroot}%{pibsdir}/ietf/
install -m0644 pibs/site/* %{buildroot}%{pibsdir}/site/
install -m0644 pibs/tubs/* %{buildroot}%{pibsdir}/tubs/
find %{buildroot}%{pibsdir}/ -name "Makefile*" | xargs rm -f

install -d %{buildroot}%{_sysconfdir}

cat > smi.conf << EOF
#
# smi.conf - Global/User SMI configuration file.
#
# See smi_config(3) for detailed information on configuration files.
#

# Extend (note the semicolon) the libsmi default module search path.
#path :%{mibsdir}/site
#path :%{mibsdir}/iana
#path :%{mibsdir}/ietf

# Add a private directory.
#path :/home/strauss/lib/mibs

# EXPERIMENTAL: Add a caching method (works only on UNIX systems). 
# NOTE: the cache directory must exist and permissions must be
# handled appropriately. A simple but insecure way is to apply
# a tmp flag to the directory (chmod 1777 /usr/local/share/mibs/cache).
#cache /usr/local/share/mibs/cache /usr/local/bin/smicache -d /usr/local/share/mibs/cache -p http://www.ibr.cs.tu-bs.de/projects/libsmi/smicache/

# Don't show any errors by default.
level 0

# Preload some basic SMIv2 modules.
load SNMPv2-SMI
load SNMPv2-TC
load SNMPv2-CONF

# Make smilint shout loud to report all errors and warnings.
smilint: level 9

# But please don't claim about any names longer than 32 chars.
# (note: this is the prefix of errors namelength-32-module,
#  -type, -object, -enumeration, and -bit)
smilint: hide namelength-32

# Preloading some more modules for special applications.
tcpdump: load DISMAN-SCRIPT-MIB
tcpdump: load IF-MIB
smiquery: load IF-MIB
EOF

install -m0644 smi.conf %{buildroot}%{_sysconfdir}/smi.conf

install -d %{buildroot}%{mibsdir}/site
install -d %{buildroot}%{pibsdir}/site

# cleanups
rm -f %{buildroot}%{_libdir}/*.*a

%post mibs-ext
## Append to config file: path for irtf and tubs
if test ! -f %{_sysconfdir}/smi.conf; then echo "# Generated by %{name}" > %{_sysconfdir}/smi.conf ; fi
for DIR in irtf tubs ; do
  if %__grep -q -e "^path.*%{mibsdir}/${DIR}" %{_sysconfdir}/smi.conf ; then continue; fi
  echo "path :%{mibsdir}/${DIR}" >> %{_sysconfdir}/smi.conf
done


%files -n %{libname}
%doc ANNOUNCE COPYING README THANKS smi.conf-example
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/smi.conf
%attr(0755,root,root) %{_libdir}/lib*.so.*

%files -n %{develname}
%doc TODO doc/draft-irtf-nmrg-sming-02.txt
%attr(0644,root,root) %{_includedir}/*.h
%attr(0755,root,root) %{_libdir}/lib*.so
%attr(0644,root,root) %{_datadir}/aclocal/*.m4
%attr(0644,root,root) %{_libdir}/pkgconfig/libsmi.pc
%attr(0644,root,root) %{_mandir}/man3/libsmi.3*
%attr(0644,root,root) %{_mandir}/man3/smi_*.3*

%files mibs-std
%dir %{mibsdir}
%dir %{mibsdir}/iana
%dir %{mibsdir}/ietf
%dir %{mibsdir}/site
%{mibsdir}/iana/*
%{mibsdir}/ietf/*

%files mibs-ext
%dir %{mibsdir}/irtf
%dir %{mibsdir}/tubs
%{mibsdir}/irtf/*
%{mibsdir}/tubs/*
%dir %{pibsdir}
%dir %{pibsdir}/ietf
%dir %{pibsdir}/site
%dir %{pibsdir}/tubs
%{pibsdir}/ietf/*
%{pibsdir}/tubs/*

%files -n smi-tools
%attr(0755,root,root) %{_bindir}/smi*
%attr(0644,root,root) %{_mandir}/man1/smi*.1*


%changelog
* Fri Apr 29 2011 Oden Eriksson <oeriksson@mandriva.com> 0.4.8-7mdv2011.0
+ Revision: 660282
- mass rebuild

* Fri Oct 22 2010 Oden Eriksson <oeriksson@mandriva.com> 0.4.8-6mdv2011.0
+ Revision: 587317
- P1: security fix for CVE-2010-2891

* Sun Mar 14 2010 Oden Eriksson <oeriksson@mandriva.com> 0.4.8-5mdv2010.1
+ Revision: 519030
- rebuild

* Wed Sep 02 2009 Christophe Fergeau <cfergeau@mandriva.com> 0.4.8-4mdv2010.0
+ Revision: 425750
- rebuild

* Sat Dec 20 2008 Oden Eriksson <oeriksson@mandriva.com> 0.4.8-3mdv2009.1
+ Revision: 316811
- fix build with -Werror=format-security (P0)

* Wed Aug 06 2008 Thierry Vignaud <tv@mandriva.org> 0.4.8-2mdv2009.0
+ Revision: 264892
- rebuild early 2009.0 package (before pixel changes)

  + Pixel <pixel@mandriva.com>
    - do not call ldconfig in %%post/%%postun, it is now handled by filetriggers

  + Oden Eriksson <oeriksson@mandriva.com>
    - 0.4.8

* Wed Dec 19 2007 Oden Eriksson <oeriksson@mandriva.com> 0.4.5-2mdv2008.1
+ Revision: 134107
- nuke remaining prereq
- rework the spec file

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request
    - fix obsolete require & replace prereq by require
    - import libsmi


* Sun Jun 18 2006 Emmanuel Andry <eandry@mandriva.org> 0.4.5-1mdv2007.0
- 0.4.5
- %%mkrel
- drop patch0 (applied upstream)

* Wed Dec 22 2004 Per Øyvind Karlsen <peroyvind@linux-mandrake.com> 0.4.3-1mdk
- 0.4.3

* Fri Feb 27 2004 Olivier Thauvin <thauvin@aerov.jussieu.fr> 0.4.1-3mdk
- Own dir (distlint)

* Thu Jul 10 2003 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.4.1-2mdk
- rebuild

* Sun Jun 29 2003 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.4.1-1mdk
- libi and macrofiction
- run make check
- added P0
- broke out the utilities into the smi-tools sub package
- misc spec file fixes

* Fri Jan 24 2003 Lenny Cartier <lenny@mandrakesoft.com> 0.4.0-2mdk
- rebuild

* Thu Aug 29 2002 Lenny Cartier <lenny@mandrakesoft.com>  0.4.0-1mdk
- 0.4.0

* Mon Aug 20 2001 Lenny Cartier <lenny@mandrakesoft.com>  0.2.16-1mdk
- updated to 0.2.16

* Mon Feb 26 2001 Lenny Cartier <lenny@mandrakesoft.com>  0.2.13-1mdk
- added in contribs by Olivier Montanuy <olivier.montanuy@wanadoo.fr> :
	- Attempt to make it conform to Mandrake packaging rules. rpmlint.

* Mon Feb 05 2001 Olivier Montanuy <olivier.montanuy@wanadoo.fr> 0.2.13-2
- First spec file for Mandrake distribution.

