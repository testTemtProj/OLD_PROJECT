/* -*- c++ -*-
 * $Id: Cookie.cc,v 1.11 2006/03/29 05:35:58 brook Exp $
 */

/*
 * ClearSilver++ Software License.
 *
 * Copyright (c) 2005,2006 Brook Milligan <brook@nmsu.edu>
 * All rights reserved.
 * 
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above
 *    copyright notice, this list of conditions and the following
 *    disclaimer in the documentation and/or other materials provided
 *    with the distribution.
 * 3. The name of the author may not be used to endorse or promote
 *    products derived from this software without specific prior
 *    written permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
 * GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include "Cookie.h"

#include <string.h>
#include <boost/date_time/posix_time/posix_time.hpp>

using namespace std;
using namespace boost;
using namespace ClearSilver;

static string convert (const posix_time::ptime& t);

// constructors
Cookie::Cookie () : name_(), 
                    value_(), 
                    credentials_()
{}

Cookie::Cookie (const char * name) : name_(name),
                                     value_(), 
                                     credentials_() 
{}

Cookie::Cookie (const char * name, const Credentials& credentials) : name_(name), 
                                                                     value_(), 
                                                                     credentials_(credentials_) 
{}

Cookie::Cookie (const char * name, const char * value) : name_(name), 
                                                         value_(value), 
                                                         credentials_() 
{}

Cookie::Cookie (const char * name, const char * value, const Credentials& credentials) : name_(name), 
                                                                                         value_(value), 
                                                                                         credentials_(credentials) 
{}

Cookie::Cookie (const string& name) : name_(name), 
                                      value_(), 
                                      credentials_() 
{}

Cookie::Cookie (const string& name, const Credentials& credentials) : name_(name), 
                                                                      value_(), 
                                                                      credentials_(credentials_) 
{}

Cookie::Cookie (const string& name, const string& value) : name_(name), 
                                                           value_(value), 
                                                           credentials_() 
{}

Cookie::Cookie (const string& name, const string& value, const Credentials& credentials) : name_(name), 
                                                                                           value_(value), 
                                                                                           credentials_(credentials) 
{}

Cookie::Cookie (const Cookie& c) : name_(c.name_), 
                                   value_(c.value_), 
                                   credentials_(c.credentials_) 
{}

Cookie::~Cookie () throw() {}

    // assignment
    Cookie&
Cookie::operator = (const Cookie& c)
{
    Cookie c_(c);
    swap (c_);
    return *this;
}

    void
Cookie::swap (Cookie& c) throw()
{
    ::swap(name_, c.name_);
    ::swap(value_, c.value_);
    ::swap(credentials_, c.credentials_);
}

// data access
    string
Cookie::name () const { return name_; }

    string
Cookie::value () const { return value_; }

    Cookie::Credentials
Cookie::credentials () const { return credentials_; }

    Cookie::Credentials&
Cookie::credentials () { return credentials_; }

    string
Cookie::to_string() const 
{
    return name_ + "=" + value_ + "; " + credentials_.to_string();
}


// constructors
Cookie::Credentials::Credentials () : authority_(), 
                                      path_(), 
                                      expires_(), 
                                      persist_(false), 
                                      secure_(false) 
{}

Cookie::Credentials::Credentials (const Authority& a) : authority_(a), 
                                                        path_(), 
                                                        expires_(), 
                                                        persist_(false), 
                                                        secure_(false) 
{}

Cookie::Credentials::Credentials (const Path& p) : authority_(), 
                                                   path_(p), 
                                                   expires_(), 
                                                   persist_(false), 
                                                   secure_(false) 
{}

Cookie::Credentials::Credentials (const Expires& e) : authority_(), 
                                                      path_(), 
                                                      expires_(e), 
                                                      persist_(true), 
                                                      secure_(false) 
{}

Cookie::Credentials::Credentials (const Authority& a, const Path& p) : authority_(a), 
                                                                       path_(p), 
                                                                       expires_(), 
                                                                       persist_(false), 
                                                                       secure_(false) 
{}

Cookie::Credentials::Credentials (const Authority& a, const Path& p, const Expires& e) : authority_(a), 
                                                                                         path_(p), 
                                                                                         expires_(e), 
                                                                                         persist_(true), 
                                                                                         secure_(false) 
{}

Cookie::Credentials::Credentials (const Credentials& c) : authority_(c.authority_), 
                                                          path_(c.path_), 
                                                          expires_(c.expires_),
                                                          persist_(c.persist_), 
                                                          secure_(c.secure_) 
{}

Cookie::Credentials::~Credentials () throw() {}

    // assignment
    Cookie::Credentials&
Cookie::Credentials::operator = (const Credentials& c)
{
    Credentials c_(c);
    swap (c_);
    return *this;
}

// swap contents
    void
Cookie::Credentials::swap (Credentials& c) throw()
{
    ::swap (authority_, c.authority_);
    ::swap (path_, c.path_);
    ::swap (expires_, c.expires_);
    ::swap (persist_, c.persist_);
    ::swap (secure_, c.secure_);
}


// data access
    Cookie::Authority
Cookie::Credentials::authority () const { return authority_; }

    Cookie::Authority&
Cookie::Credentials::authority () { return authority_; }

    Cookie::Path
Cookie::Credentials::path () const { return path_; }

    Cookie::Path&
Cookie::Credentials::path () { return path_; }

    Cookie::Expires
Cookie::Credentials::expires () const { return expires_; }

    Cookie::Expires&
Cookie::Credentials::expires ()
{
    persist_ = true;
    return expires_;
}

    bool
Cookie::Credentials::persist () const { return persist_; }

    bool
Cookie::Credentials::secure () const { return secure_; }

    bool&
Cookie::Credentials::secure () { return secure_; }

    string
Cookie::Credentials::to_string () const
{
    return "expires=" + expires_() + "; path=" + path_() + "; domain=" + authority_();
}


// constructors
Cookie::Authority::Authority () : authority_() {}
Cookie::Authority::Authority (const char * a) : authority_(a?string(a):"") {}
Cookie::Authority::Authority (const string& a) : authority_(a) {}
Cookie::Authority::Authority (const Authority& a) : authority_(a.authority_) {}
Cookie::Authority::~Authority () throw() {}

// assignment
    Cookie::Authority&
Cookie::Authority::operator = (const Authority& a)
{
    Authority a_ (a);
    swap (a_);
    return *this;
}

// swap contents
    void
Cookie::Authority::swap (Authority& a) throw()
{
    ::swap(authority_, a.authority_);
}

// inspectors
    bool
Cookie::Authority::empty () const { return authority_.empty(); }

// conversions
    string
Cookie::Authority::operator () () const { return authority_; }


// constructors
Cookie::Path::Path () : path_() {}
Cookie::Path::Path (const char * p) : path_(p?string(p):"") {}
Cookie::Path::Path (const string& p) : path_(p) {}
Cookie::Path::Path (const Path& p) : path_(p.path_) {}
Cookie::Path::~Path () throw() {}

// assignment
    Cookie::Path&
Cookie::Path::operator = (const Path& p)
{
    Path p_(p);
    swap (p_);
    return *this;
}


    void
Cookie::Path::swap (Path& p) throw()
{
    ::swap(path_, p.path_);
}
// inspectors
    bool
Cookie::Path::empty () const { return path_.empty(); }

// conversions
    string
Cookie::Path::operator () () const { return path_; }


// constructors
Cookie::Expires::Expires () : expires_() 
{}

Cookie::Expires::Expires (const char* e) : expires_(convert(posix_time::time_from_string(e))) 
{}

Cookie::Expires::Expires (const string& e) : expires_(convert(posix_time::time_from_string(e))) 
{}

Cookie::Expires::Expires (time_t t) : expires_(convert(posix_time::from_time_t(t))) 
{}

Cookie::Expires::Expires (struct tm tm) : expires_(convert (posix_time::ptime (gregorian::date(tm.tm_year, tm.tm_mon, tm.tm_mday), posix_time::time_duration(tm.tm_hour, tm.tm_min, tm.tm_sec)))) 
{}

Cookie::Expires::Expires (const boost::posix_time::ptime& expires) : expires_(convert(expires)) 
{}

Cookie::Expires::Expires (const Expires& e) : expires_(e.expires_) 
{}

Cookie::Expires::~Expires () throw() {}

    // assignment
    Cookie::Expires&
Cookie::Expires::operator = (const Expires& e)
{
    expires_ = e.expires_;
    return *this;
}

// swap contents
    void
Cookie::Expires::swap (Expires& e) throw()
{
    std::swap(expires_, e.expires_);
}

// inspectors
Cookie::Expires::operator bool () const { return !expires_.empty(); }

    bool
Cookie::Expires::empty () const { return expires_.empty(); }

// conversions
    string
Cookie::Expires::operator () () const { return expires_; }

    string
convert (const posix_time::ptime& t)
{
    ostringstream ss;
    ss.exceptions(ios_base::failbit);

    date_time::time_facet<posix_time::ptime, char>* facet
        = new date_time::time_facet<posix_time::ptime, char>;
    ss.imbue(locale(locale::classic(), facet));

    facet->format("%a, %d-%b-%Y %T GMT");
    ss.str("");
    ss << t;
    return ss.str();
}
